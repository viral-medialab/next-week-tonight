from pymongo.mongo_client import MongoClient

def connect_to_mongodb():
    mongo_uri = "mongodb+srv://viralgrads3:viralgrads3@sandbox.h8gtitv.mongodb.net"
    client = MongoClient(mongo_uri)
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)

    db = client["news"]
    collection = db["articles"]
    
    return client


if __name__=='__main__':
    connect_to_mongodb()