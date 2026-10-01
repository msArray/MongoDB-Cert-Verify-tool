from pymongo import MongoClient, UpdateOne
from pymongo.server_api import ServerApi


class MongoAdaptor:
    def __init__(self, uri):
        self.uri = uri
        self.client = MongoClient(self.uri, server_api=ServerApi("1"))
        self.db_que = []

        try:
            self.database = self.client.get_database("verify_mongo_cert")
            self.sd_marks = self.database.get_collection("SD_Marks")

            # stu_name の重複をDB側でも防止
            self.sd_marks.create_index("stu_name", unique=True)

        except Exception as e:
            raise Exception(
                "Unable to find the document due to the following error: ", e
            )

    def insert_que(self, stu_name, score, rational, sub_date, cert_num):
        self.db_que.append(
            {
                "stu_name": stu_name,
                "cert_info": {
                    "score": score,
                    "rational": rational,
                    "sub_date": sub_date,
                    "cert_num": cert_num,
                },
            }
        )

    def q_apply_db(self):
        if not self.db_que:
            return

        operations = []

        for data in self.db_que:
            operations.append(
                UpdateOne(
                    {"stu_name": data["stu_name"]},
                    {"$push": {"cert_info": data["cert_info"]}},
                    upsert=True,
                )
            )

        result = self.sd_marks.bulk_write(operations)

        # 正常にDBへ反映されたらキューを空にする
        self.db_que.clear()

        return result

    def get_collection(self):
        return self.sd_marks
