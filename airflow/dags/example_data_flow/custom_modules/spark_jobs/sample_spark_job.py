from pyspark.sql import SparkSession


# 함수 형태로 작성 => 이 함수를 Python Operator로 감싸서 spark connect 서버에 제출 => remote 부분 참고
def run_sample_etl_job():
    spark = (
        SparkSession.builder.remote(
            "sc://spark-connect-server.spark.svc.cluster.local:15002"
        )
        .appName("daily-etl-job")
        .getOrCreate()
    )

    df = spark.read.parquet("s3a://bronze-data/events/2024-03-15/")
    transformed_df = df.groupBy("user_id").agg({"amount": "sum"})
    transformed_df.write.parquet("s3a://silver-data/aggregates/2024-03-15/")

    spark.stop()
