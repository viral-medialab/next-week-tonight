const { MongoClient } = require('mongodb');

const connectToMongo = async () => {
    let mongoClient;

    try {
        console.log("test: ", process.env.MONGODB_URI);
        mongoClient = new MongoClient(process.env.MONGODB_URI);
        console.log('Connecting to MongoDB Atlas cluster...');
        await mongoClient.connect();
        console.log('Successfully connected to MongoDB Atlas!');
 
        return mongoClient;
    } catch (error) {
        console.error('Connection to MongoDB Atlas failed!', error);
        process.exit();
    }
}

const getChangeStream = async (dbName, collectionName) => {
    const mongoClient = await connectToMongo();
    const db = mongoClient.db(dbName);
    const topics = db.collection(collectionName);
    const changeStream = topics.watch();

    return changeStream;
    
}

module.exports = { getChangeStream, connectToMongo };
