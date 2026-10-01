import os
import re
from datetime import datetime
import unicodedata

from PySide6.QtCore import QObject, Signal, Slot
from pypdf import PdfReader

from app.services.mongo_adaptor import MongoAdaptor


class VerifyPDFsWorker(QObject):
    progress = Signal(int)
    finished = Signal(object)
    error = Signal(str)

    def __init__(
        self, dirs, target_dir, target_date, input_cert_name, db_adap: MongoAdaptor
    ):
        super().__init__()

        self.dirs = dirs
        self.target_dir = target_dir
        self.target_date = target_date
        self.input_cert_name = input_cert_name
        self.db_client = db_adap
        self.dir_re = re.compile(
            r"^\d+-\d+\s+-\s+"
            r"(?P<name>.+?)"
            r"\s+(?P<certname>SOI-[A-Za-z]+)"
            r"\s+-\s+"
            r"(?P<datetime>\d{1,2} [A-Za-z]+ \d{4})"
            r"\s+\d{1,2}_\d{2} (?:AM|PM)$"
        )

    @Slot()
    def run(self):
        try:
            pdf_txts = []
            for i, dir in enumerate(self.dirs):
                self.progress.emit(i)
                files = os.listdir(f"{self.target_dir}/{dir}")
                for file in files:
                    if os.path.splitext(f"{self.target_dir}/{dir}/{file}")[1] != ".pdf":
                        continue
                    reader = PdfReader(f"{self.target_dir}/{dir}/{file}")
                    page = reader.pages[0]
                    pdf_txts.append(page.extract_text())
                    obj = re.fullmatch(self.dir_re, dir)
                    if obj:
                        # print(obj.group("name"))
                        # print(obj.group("certname"))
                        # print(obj.group("datetime"))
                        pass
                    txts = page.extract_text().split("\n")
                    if len(txts) == 4:
                        usr_name = txts[0]
                        cert_id = txts[1]
                        cert_date = txts[2]
                        cert_name = txts[3]

                        if not self.name_validate(obj.group("name"), usr_name):
                            self.insert_fail(
                                obj.group("name"),
                                f'Please modify the certificate name so that it becomes "{obj.group("name")}".',
                                obj.group("datetime"),
                                cert_id,
                            )
                            continue
                        # print(obj.group("name"), usr_name)

                        point = self.date_to_point(
                            cert_date, obj.group("datetime"), self.target_date
                        )

                        if not self.certname_validate(cert_name, self.input_cert_name):
                            self.insert_fail(
                                obj.group("name"),
                                "Mismatch between the certificate name and the Unit name contained in the folder.",
                                obj.group("datetime"),
                                cert_id,
                            )
                            continue

                        if re.fullmatch(r"MDB[0-9A-Za-z]+", cert_id) is None:
                            self.insert_fail(
                                obj.group("name"),
                                "The certificate ID is not in the correct format.",
                                obj.group("datetime"),
                                cert_id,
                            )
                            continue

                        if point == 2:
                            self.db_client.insert_que(
                                obj.group("name"),
                                point,
                                "It has been submitted correctly and on time.",
                                datetime.strptime(obj.group("datetime"), "%d %B %Y"),
                                cert_id,
                            )
                        else:
                            self.db_client.insert_que(
                                obj.group("name"),
                                point,
                                "Overdue",
                                datetime.strptime(obj.group("datetime"), "%d %B %Y"),
                                cert_id,
                            )

                    self.err = [dir, file]

            self.db_client.q_apply_db()
            self.finished.emit(pdf_txts)

        except Exception as e:
            print(self.err)
            self.error.emit(str(e))

    def normalize_name(self, name: str) -> str:
        name = unicodedata.normalize("NFKC", name)

        name = name.lower()

        # 記号を空白に
        name = re.sub(r"[^a-z0-9\s]", " ", name)

        # 連続する空白を1つに
        name = re.sub(r"\s+", " ", name)

        return name.strip()

    def name_validate(self, first: str, second: str) -> bool:
        a = self.normalize_name(first)
        b = self.normalize_name(second)

        # 空白で分割
        a_parts = a.split()
        b_parts = b.split()

        # 順番を無視して比較
        print(sorted(a_parts) == sorted(b_parts), a_parts, b_parts)
        return sorted(a_parts) == sorted(b_parts)

    def date_to_point(
        self,
        cert_date,
        folder_date,
        target_date,
    ):
        if (
            datetime.strptime(cert_date, "%m-%d-%Y").date()
            <= datetime.strptime(folder_date, "%d %B %Y").date()
            and datetime.strptime(cert_date, "%m-%d-%Y").date()
            <= datetime.strptime(target_date, "%a %b %d %Y").date()
        ):
            return 2
        return 1

    def certname_validate(self, cert_name, input_cert):
        if cert_name == input_cert:
            return True

        return False

    def insert_fail(self, stu_name, reason, date_time, cert_num):
        self.db_client.insert_que(
            stu_name,
            0,
            reason,
            datetime.strptime(date_time, "%d %B %Y"),
            cert_num,
        )
        pass
