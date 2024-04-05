# Next Week Tonight
[Document](https://docs.google.com/document/d/1i82OncJFmE4UVjzzamfDoAXFJ58ildoBO9mC9NspEew/edit) for more details. 
[Generative AI for News](https://docs.google.com/presentation/d/1RDVTPms0JYfouxjgdvnZfe4yi8U-xZBbFdZqJaAXP4E/edit#slide=id.g35f391192_00) Presentation

Next week tonight is a predictive analytical tool that gives a summary of next week's news stories to you today -- it updates the news stories based on user input but also using historical context and data. 

We are passionate about bringing interactivity to news story telling and providing a glimpse into how tuning different parameters can generative different possible futures and outcomes. 


# Instructions

Currently how we run this is:

Open up one terminal and run 
> python Backendv2/app.py

Open up a second terminal and run 
> npm install (if running for the first time)
> cd frontend 

> npm run dev

Then navigate to the localhost for the frontend and click an article and run any question. Right now, the question you type will not matter as the inputs are fixed. When Allen sets up the new database with the website (we have to change the DB architecture to match news-dive), we will be able to run flexible inputs. When you run any question through the chat, go to the terminal that is running the backend and you will see the output there. If it returns code 200 after printing the outputs, then the code works.
