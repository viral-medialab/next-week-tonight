const { ObjectId } = require("mongodb");

async function getArticlesContents(articles) {
    // article url looks like this: https://www.msn.com/en-us/news/world/iran-says-it-has-started-enriching-uranium-to-60-percent/ar-BB1fJ5Qq?ocid=msedgntp
    // use regex to get BB1fJ5Qq
    console.log("Getting article ids" + articles.map((article) => article.url));
    const articleIds = articles.map((article) => {
        const match = article.url.match(/\/ar-(.*?)(?:\?|$)/);
        return match && match.length > 1 ? match[1] : null;
    });
    console.log("articleIds", articleIds);
    console.log("Getting article contents");
    const articleContents = await Promise.all(
        articleIds.map(async (articleId) => {
            const articleContentUrl = `https://assets.msn.com/content/view/v2/Detail/en-us/${articleId}`;
            const articleContentResponse = await fetch(articleContentUrl);
            const articleContentData = await articleContentResponse.json();
            return articleContentData.body;
        })
    );
    console.log("articleContents", articleContents);
    return articleContents;
}

const getArticles = async (db, topic) => {
    console.log("Checking if topics exist in database");
    //get id from req
    const topicId = new ObjectId(topic._id);
    const collection = db.collection("articles");
    const query = { _id: topicId };
    const articleDoc = await collection.findOne(query);
    if (articleDoc) {
        console.log("Article exist in database", articleDoc);
        return articleDoc;
    }
    // get topic with id
    if (topic) {
        console.log("Topic exists in database");
        // see if articles are processed
        const newsHeaders = {
            "Ocp-Apim-Subscription-Key": process.env.BING_NEWS_API_KEY || "",
        };
        const newsUrl = `https://api.bing.microsoft.com/v7.0/news/search?q=${topic.topic}+site=msn.com&count=10`;
        const newsResponse = await fetch(newsUrl, {
            headers: newsHeaders,
        });
        const newsData = await newsResponse.json();
        console.log("newsData", newsData);

        const articles = newsData.value.filter((article) => article.url.includes("msn.com")).slice(0,10);
        
        console.log("articles length ", articles.length);
        // get article content -- debugging for limiting articles 

        const articlesContentsResponse = await getArticlesContents(articles);
        articles.forEach((article, index) => {
            article._id = new ObjectId();
            article.content = articlesContentsResponse[index];
        });

        // insert articles as is to database under topic collection, under the topic with the id
        const articlesDoc = {
            _id: topicId,
            topic: topic.topic,
            articles: articles,
        };

        console.log("articles debug", articlesDoc);
        // save articles to database in articles collection
        const articlesCollection = db.collection("articles");
        await articlesCollection.insertOne(articlesDoc);
        console.log("Articles saved to database under topic: " + topic.topic);
        // return saved topic 
        return articlesDoc;
    } else {
        throw new Error(`Topic ${topicId} does not exist in database`);
    }
};
module.exports = { getArticles };
