import { NextApiRequest, NextApiResponse } from "next";
import fetch from "node-fetch";

export default async (req: NextApiRequest, res: NextApiResponse) => {

    let attempts = 0;
    const maxAttempts = 2;

    while(attempts < maxAttempts) {
        try {
            //parse JSON body
            const { allArticles, currentArticle, topicName, messages } = JSON.parse(
                req.body
            );
            //prompt
            // const newsData = newsData.value.map((article: any) => ({
            //     title: article.name,
            //     description: article.description,
            //     content: article.content,
            // }));
            // messages: [
            //     { role: "system", content: "You are a helpful assistant." },
            //     { role: "user", content: topicPrompt },
            // ],
            console.log("Sending chat request");
            const openAIHeaders = {
                "Content-Type": "application/json",
                Authorization: "Bearer " + process.env.OPENAI_API_KEY,
            };
            console.log("currentArticle", currentArticle);
            const firstPrompt = (() => {
                // Start with the current article (if it exists)
                let prompt = `You are a super smart journalist that can uncover the truth of a story from different sources. Here are the articles you will be helping me to analyze:\nTopic: ${topicName}\nNews headlines and descriptions:\n`;
            
                if (currentArticle) {
                    prompt += `Title: ${currentArticle.name}\n
                    Content: ${currentArticle.content}\n
                    Source: ${currentArticle.provider[0].name.replace("on MSN.com", "")}\n
                    The above article is the one I am currently reading.\n\n`;
                }
            
                // Filter out the current article and add the others
                const otherArticles = allArticles
                    .filter((article: any) => !currentArticle || article.name !== currentArticle.name)
                    .slice(0, 3)
                    .map(
                        (article: any, idx: number) =>
                            `Article ${idx + 1}\n Title: ${article.name}\n 
                            Content: ${article.content.substring(0, Math.min(article.content.length, 16000/3))}\n 
                            Source: ${article.provider[0].name.replace("on MSN.com", "")}\n`
                    )
                    .join("\n");
            
                prompt += otherArticles;
            
                // Truncate to approximately 16,000 characters
                return prompt.length > 16000 ? prompt.substring(0, 15997) + "..." : prompt;
            })();
            
            console.log(firstPrompt);
            

            //OpenAI api body
            console.log("firstPrompt", firstPrompt);
            console.log("messages", messages);
            const openAIBody = {
                model: "gpt-3.5-turbo",
                messages: [
                    { role: "system", content: "You are a helpful assistant." },
                    { role: "user", content: firstPrompt },
                    ...messages,
                ],
            };
            console.log("openAIBody0", openAIBody);

            const openAIResponse = await fetch(
                "https://api.openai.com/v1/chat/completions",
                {
                    method: "POST",
                    headers: openAIHeaders,
                    body: JSON.stringify(openAIBody),
                }
            );
            const openAIData: any = await openAIResponse.json();
            console.log("openAIData", openAIData);
            console.log("chat response", openAIData.choices[0].message.content);

            const response: string = openAIData.choices[0].message.content;

            res.setHeader("Cache-Control", "public, max-age=3600");
            res.end(response);
            break;
        } catch (error) {
            attempts++;
            console.error(error);
            res.status(500).end();
        }
    }
};
