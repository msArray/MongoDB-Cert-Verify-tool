from openpyxl import Workbook
from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi


async def export_excel(mongo_uri, path):
    client = AsyncMongoClient(
        mongo_uri,
        server_api=ServerApi("1"),
    )

    sd_marks = client.get_database("verify_mongo_cert").get_collection("SD_Marks")

    wb = Workbook()
    ws = wb.active
    ws.title = "SD Marks"

    # ヘッダー
    ws.append(
        [
            "Student Name",
            "Total Score",
        ]
    )

    pipeline = [
        {
            "$project": {
                "_id": 0,
                "stu_name": 1,
                # cert_info 内の score をすべて合計
                "total_score": {"$sum": "$cert_info.score"},
            }
        },
        {"$sort": {"stu_name": 1}},
    ]

    cursor = await sd_marks.aggregate(pipeline)

    results = []

    async for result in cursor:
        stu_name = result.get("stu_name", "")
        total_score = result.get("total_score", 0)

        print(stu_name, total_score)

        results.append(result)

        ws.append(
            [
                stu_name,
                total_score,
            ]
        )

    wb.save(path)

    await client.close()

    return results
