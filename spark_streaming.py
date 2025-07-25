from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, DoubleType
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import LogisticRegressionModel
from pymongo import MongoClient
import json

# Spark oturumu başlat
spark = SparkSession.builder \
    .appName("FraudDetectionStream") \
    .getOrCreate()

# Kafka'dan gelecek JSON verisinin şeması
schema = StructType() \
    .add("V1", DoubleType()).add("V2", DoubleType()).add("V3", DoubleType()) \
    .add("V4", DoubleType()).add("V5", DoubleType()).add("V6", DoubleType()) \
    .add("V7", DoubleType()).add("V8", DoubleType()).add("V9", DoubleType()) \
    .add("V10", DoubleType()).add("V11", DoubleType()).add("V12", DoubleType()) \
    .add("V13", DoubleType()).add("V14", DoubleType()).add("V15", DoubleType()) \
    .add("V16", DoubleType()).add("V17", DoubleType()).add("V18", DoubleType()) \
    .add("V19", DoubleType()).add("V20", DoubleType()).add("V21", DoubleType()) \
    .add("V22", DoubleType()).add("V23", DoubleType()).add("V24", DoubleType()) \
    .add("V25", DoubleType()).add("V26", DoubleType()).add("V27", DoubleType()) \
    .add("V28", DoubleType()).add("normAmount", DoubleType()).add("Class", DoubleType())

# Kafka'dan veri oku
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "transaction-data") \
    .option("startingOffsets", "latest") \
    .load()

# JSON veriyi parse et
veri_df = kafka_df.selectExpr("CAST(value AS STRING) as json") \
    .select(from_json(col("json"), schema).alias("veri")) \
    .select("veri.*")

# Özellik sütunlarını belirle
ozellikler = [c for c in veri_df.columns if c != "Class"]

# Eğitilmiş modeli yükle
model = LogisticRegressionModel.load("model/fraud_model")

# Özellikleri vektöre dönüştür
assembler = VectorAssembler(inputCols=ozellikler, outputCol="features")
veri_vec = assembler.transform(veri_df)

# Modelle tahmin yap
tahmin_df = model.transform(veri_vec).select("features", "prediction", "Class", *ozellikler)

# MongoDB’ye yazma fonksiyonu
def yazdir(batch_df, epoch_id):
    frauds = batch_df.filter(batch_df["prediction"] == 1).toJSON().collect()
    print(f"✔️ Epoch {epoch_id} - Tespit edilen sahtekarlık sayısı: {len(frauds)}")
    if frauds:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["fraudDB"]
        collection = db["alerts"]
        for json_str in frauds:
            collection.insert_one(json.loads(json_str))
        client.close()

# Streaming işlemini başlat
query = tahmin_df.writeStream \
    .foreachBatch(yazdir) \
    .outputMode("update") \
    .start()

query.awaitTermination()
