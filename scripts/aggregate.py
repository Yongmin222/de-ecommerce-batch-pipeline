from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as _sum, count, to_date

# 1. Spark 세션 생성 (클러스터에 연결)
spark = SparkSession.builder \
    .appName("EcommerceAggregation") \
    .master("spark://spark-master:7077") \
    .config("spark.jars", "/opt/bitnami/spark/jars/mysql-connector-j.jar") \
    .config("spark.executor.memory", "3g") \
    .getOrCreate()

# 2. MySQL에서 데이터 읽어오기
df = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:mysql://mysql-de:3306/de_portfolio") \
    .option("dbtable", "events") \
    .option("user", "root") \
    .option("password", "de1234!") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("partitionColumn", "user_id") \
    .option("lowerBound", "1") \
    .option("upperBound", "600000000") \
    .option("numPartitions", "8") \
    .option("fetchsize", "1000") \
    .load()

print(f"읽어온 행 수: {df.count()}")

# 3. 일별 매출 집계 (purchase 이벤트만 대상)
daily_revenue = df.filter(col("event_type") == "purchase") \
    .withColumn("event_date", to_date(col("event_time"))) \
    .groupBy("event_date") \
    .agg(
        _sum("price").alias("total_revenue"),
        count("*").alias("purchase_count")
    ) \
    .orderBy("event_date")

daily_revenue.show(31)
daily_revenue.write \
    .format("jdbc") \
    .option("url", "jdbc:mysql://mysql-de:3306/de_portfolio") \
    .option("dbtable", "daily_revenue") \
    .option("user", "root") \
    .option("password", "de1234!") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .mode("overwrite") \
    .save()

print("daily_revenue 테이블 저장 완료")

# 4. 브랜드별 조회수 Top 10
brand_views = df.filter(col("event_type") == "view") \
    .groupBy("brand") \
    .count() \
    .orderBy(col("count").desc())

brand_views.show(10)
brand_views.write \
    .format("jdbc") \
    .option("url", "jdbc:mysql://mysql-de:3306/de_portfolio") \
    .option("dbtable", "brand_views") \
    .option("user", "root") \
    .option("password", "de1234!") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .mode("overwrite") \
    .save()

print("brand_views 테이블 저장 완료")

spark.stop()
