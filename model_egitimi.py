from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import LogisticRegression  # Alternatif: RandomForestClassifier
import os

# Spark oturumunu başlat
spark = SparkSession.builder \
    .appName("FraudDetectionModelTraining") \
    .getOrCreate()

# Eğitim verisini oku
veri_yolu = "data/train.csv"
df = spark.read.csv(veri_yolu, header=True, inferSchema=True)

# Özellik sütunlarını belirle
ozellikler = df.columns
ozellikler.remove("Class")  # Hedef sütun

# VectorAssembler ile özellikleri tek sütunda birleştir
assembler = VectorAssembler(inputCols=ozellikler, outputCol="features")
veri = assembler.transform(df).select("features", "Class")

# Logistic Regression modeli tanımla
model = LogisticRegression(labelCol="Class", featuresCol="features")

# Modeli eğit
egitilmis_model = model.fit(veri)

# Modeli kaydet
os.makedirs("model", exist_ok=True)
egitilmis_model.save("model/fraud_model")

# Spark oturumunu kapat
spark.stop()
