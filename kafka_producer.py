import pandas as pd
import json
import time
from sklearn.preprocessing import StandardScaler
from kafka import KafkaProducer

# creditcard.csv'yi oku ve karıştır
df = pd.read_csv("data/creditcard.csv")
df = df.sample(frac=1).reset_index(drop=True)

# normAmount hesapla
df["normAmount"] = StandardScaler().fit_transform(df["Amount"].values.reshape(-1, 1))

# Amount ve Time sütunlarını çıkar
df = df.drop(["Amount", "Time"], axis=1)

# Kafka Producer oluştur
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

# Her satırı Kafka'ya gönder
for index, row in df.iterrows():
    veri = row.to_dict()
    producer.send('transaction-data', value=veri)
    print(f"[{index}] Gönderildi: {veri}")
    time.sleep(0.1)  # isteğe bağlı bekleme süresi

producer.flush()
producer.close()
