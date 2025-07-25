from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import LogisticRegressionModel  # Eğer RandomForest kullandıysan burayı değiştir
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

# Spark oturumu başlat
spark = SparkSession.builder \
    .appName("FraudDetectionModelTesting") \
    .getOrCreate()

# Test verisini yükle
df = spark.read.csv("data/test.csv", header=True, inferSchema=True)

# Özellikleri birleştir
ozellikler = df.columns
ozellikler.remove("Class")

assembler = VectorAssembler(inputCols=ozellikler, outputCol="features")
veri = assembler.transform(df).select("features", "Class")

# Eğitilmiş modeli yükle
model = LogisticRegressionModel.load("model/fraud_model")

# Tahmin yap
tahminler = model.transform(veri)

# Başarı metrikleri
degerlendirici_acc = MulticlassClassificationEvaluator(labelCol="Class", predictionCol="prediction", metricName="accuracy")
degerlendirici_f1 = MulticlassClassificationEvaluator(labelCol="Class", predictionCol="prediction", metricName="f1")
degerlendirici_precision = MulticlassClassificationEvaluator(labelCol="Class", predictionCol="prediction", metricName="weightedPrecision")
degerlendirici_recall = MulticlassClassificationEvaluator(labelCol="Class", predictionCol="prediction", metricName="weightedRecall")

# Metrikleri yazdır
print("Doğruluk (Accuracy):", degerlendirici_acc.evaluate(tahminler))
print("F1 Skoru:", degerlendirici_f1.evaluate(tahminler))
print("Precision:", degerlendirici_precision.evaluate(tahminler))
print("Recall:", degerlendirici_recall.evaluate(tahminler))

# Spark oturumunu kapat
spark.stop()
