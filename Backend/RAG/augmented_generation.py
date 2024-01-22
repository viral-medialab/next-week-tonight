import sys
sys.path.append("../DataPipeline")
from dotenv import load_dotenv
import os
load_dotenv("../../vars.env")
from openai import OpenAI
openai_api = os.environ.get("OPENAI_API")
from retrieval import get_embedding, find_closest_article_using_simple_search, fetch_embeddings_from_mongo
all_doc_embeddings = fetch_embeddings_from_mongo()
import re
import requests
from bs4 import BeautifulSoup


def fetch_article_contents(article_id):
    '''
    Returns article's author and contents of the article
    '''
    asset_url = "https://assets.msn.com/content/view/v2/Detail/en-us/" + article_id

    try:
        response = requests.get(asset_url)
        response.raise_for_status()
        data = response.json()
        html_content = data.get('body', 'No content found')

    except requests.RequestException as e:
        print(f"Error fetching article: {e}")
        return None
    
    
    soup = BeautifulSoup(html_content, 'lxml')
    paragraphs = [p.get_text(separator=' ', strip=True) for p in soup.find_all('p')]
    #print(author)
    return '\n\n'.join(paragraphs)


def fetch_and_summarize_articles(relevant_articles):
    content = [fetch_article_contents(article) for article in relevant_articles]
    combined_summaries = summarize_articles(content)
    return combined_summaries



def summarize_articles(text_from_articles):
    context_prompt = "As a professional summarizer, create a concise and comprehensive summary of the provided text, be it an article, post, conversation, or passage, while adhering to these guidelines: \n\nCraft a summary that is detailed, thorough, in-depth, and complex, while maintaining clarity and conciseness. \n\nIncorporate main ideas and essential information, eliminating extraneous language and focusing on critical aspects. \n\nRely strictly on the provided text, without including external information. \n\nFormat the summary in paragraph form for easy understanding. \n\nConclude your notes with [End of Notes, Message #X] to indicate completion, where 'X' represents the total number of messages that I have sent. In other words, include a message counter where you start with #1 and add 1 to the message counter every time I send a message. \n\nBy following this optimized prompt, you will generate an effective summary that encapsulates the essence of the given text in a clear, concise, and reader-friendly manner."
    query_prompts = text_from_articles

    updated_query_chatgpt(context_prompt, query_prompts)



def generate_relevant_questions(article_context, user_prompt):
    context_prompt = '''You are a fusion of two great minds, drawing from the great predictive power of Nostradamus and the excellent detective work 
    of Sherlock Holmes. I am going to ask you a hypothetical question about things you were not trained on and you will perform detective work based 
    on your vast knowledge base. When I give you the question, you must provide any amount of Google search prompts that will best help
    you answer the original question. Do not elaborate as to why you chose these questions, and separate each question by a semicolon. The questions 
    should be filled with keywords that will help you generate the best responses to your queries. Make sure you cast a wide net for the scope of all
    questions combined. To emphasize, do not use the same keywords for all questions. There is no need for brief questions, take your time and 
    take a deep breath and then write your questions as long as you need. These questions will be fed into an oracle and you will have no
    other chance to ask questions, so make sure you ask the most relevant yet most encompassing questions possible and make sure you understand 
    EVERYTHING that you are not asking a question for. Make sure you also understand why the question is being asked.
    
    For example, on an article about the Houthi's retaliation against America during the 2023 Gaza war, do not ask questions only about the Houthis, but make sure you ask a question that will help you understand the context of what the Gaza war is and why the Houthis are involved.'''.replace("\n", "")
    article_context = "Here is an article that you will use to aid your question making: " + article_context
    return updated_query_chatgpt([context_prompt, article_context], [user_prompt])




def generate_article(user_prompt, relevant_info):
    #Relevant info is a list of strings where each string is an article body

    overall_context = '''You are a top-notch journalist who writes high-quality opinion pieces that speculate about the future given 
    present-day information. Your articles use formal language and use only factual information. You have a great mind that pulls from
    both system-provided context and your access to your massive training corpus. Your articles are roughly 500 words in length and split
    up into many small paragraphs, reading like a piece from a high regarded publisher like The Associated Press, CNN, Fox, or NBC news. 
    Begin your article by analyzing why the query was posed, and then respond to the query. Please include an article title followed by 
    a roughly 500 word article.'''.replace("\n", "")

    relevant_context = "Here is some relevant information to write your articles. Use the information here to extract facts for your articles (each piece of information is separated by a semicolon): ".replace("\n", "")
    for info in relevant_info:
        relevant_context += info + ";"
    relevant_context = relevant_context[:-1]

    user_query = 'Please write an article using the context to answer the following question: ' + user_prompt

    return updated_query_chatgpt([overall_context, relevant_context], user_query)



def updated_query_chatgpt(contexts, queries):
    # Query ChatGPT and return the response (this function needs to be defined)
    # Set your OpenAI API key
    openai_api = os.environ.get("OPENAI_API")

    client = OpenAI(
        #  This is the default and can be omitted
        api_key=openai_api,
    )

    if len(queries) > 1:
        contexts += ["Note: The input will be split by semicolons. Answer each prompt separately and return your answer also split by semicolons. For example, if I asked you to solve arithmetic problems and my input was '2+2;4+5', your answer should be '4;9'."]
    messages = []
    for context in contexts:
        messages.append({"role": "system", "content": context})
    final_query = ""
    for query in queries:
        final_query += query + ";"
    messages.append({"role": "user", "content": final_query[:-1]})
    response = client.chat.completions.create(
        messages=messages,
        model="gpt-4-1106-preview",
    )

    return response.choices[0].message.content.split(";")


def fetch_article_id(article_url):        
    pattern = re.compile(r'/ar-([A-Za-z0-9]+)')

    match = pattern.search(article_url)
    if match:
        article_id = match.group(1)
        return article_id
    else:
        raise Exception("No article ID found")


def q2a_workflow(article, user_prompt, num_articles, verbose = True):
    '''
    Takes an article and corresponding user query, and works it into an article that answers the user's prompt.

    The workflow is as follows:

        1)  Input:  User prompt, article
            Output: Questions that help answer user prompt

        2)  Input:  User prompt, Questions that help answer user prompt
            Output: Embeddings of these questions and user input

        3)  Input:  Embedding of user prompt and AI-generated questions
            Output: Set of articles that provide good context

        4)  Input:  User input, set of articles that provide good context
            Output: AI-generated article 
    '''
    i = 0
    if verbose:
        i += 1
        print(f"At stage {i}")
    AI_generated_questions = generate_relevant_questions(article, user_prompt)
    if verbose:
        i += 1
        print(f"At stage {i}")
    embeddings = [get_embedding(user_prompt)] + [get_embedding(question) for question in AI_generated_questions]
    if verbose:
        i += 1
        print(f"At stage {i}")
    relevant_article_urls = [find_closest_article_using_simple_search(embedding, all_doc_embeddings) for embedding in embeddings]
    if verbose:
        i += 1
        print(f"At stage {i}")
    relevant_articles = [fetch_article_contents(fetch_article_id(url)) for url in set(relevant_article_urls[:num_articles])]
    
    out = generate_article(user_prompt, relevant_articles)
    if verbose:
        print("AI generated questions: ", AI_generated_questions)
        print("Relevant articles: ", relevant_articles)
        print("\n\n\n\n\n\n")
        print("Created article:", out)
    return AI_generated_questions, relevant_articles, out


def save_to_file(data, filename="out_article.txt"):
    with open(filename, 'w') as file:
        for entry in data:
            if isinstance(entry, list):
                for item in entry:
                    file.write(f"{item}\n")
            else:
                file.write(entry + "\n")
            file.write("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")



if __name__ == '__main__':
    query = "What if the Houthis in Yemen retaliate against the American for their strikes?"
    article = "'This live coverage has ended. For the latest updates, please go here .\n\nThe United States fired its second round of strikes in less than 24 hours against Houthi militants in Yemen on Thursday morning, targeting “a couple of anti-ship missiles that we had reason to believe were being prepared for imminent fire into the southern Red Sea,” National Security Council spokesman John Kirby said. Israel stepped up raids in the occupied West Bank on Thursday, saying security forces had been operating in the Tulkarm refugee camp for over 35 hours.\n\n8:38 PM: U.S. launches new round of strikes against Yemen’s Houthis; Houthis attack another ship\n\nThe United States fired another round of strikes Thursday morning against Houthi militants in Yemen , targeting “a couple of anti-ship missiles that we had reason to believe were being prepared for imminent fire into the southern Red Sea,” National Security Council spokesman John Kirby said. Later in the day, the Houthis attacked another U.S.-owned ship — the third attack on commercial shipping vessels in three days, the United States said.\n\nThe U.S. strikes, which the Pentagon said were carried out by Navy fighter jets, were the second in less than 24 hours . The U.S. Navy on Wednesday night struck 14 missiles it said the Houthis had “loaded to be fired” against merchant vessels and American warships, according to U.S. Central Command.\n\nKirby said President Biden authorized the strikes as commander in chief under Article II authorities in the Constitution, and under Article 51 of the U.N. charter authorizing self-defense.\n\nHouthi militants have been undeterred by U.S. strikes, continuing to attack commercial vessels. On Thursday night local time in Yemen, Houthi militants launched two anti-ship ballistic missiles at M/V Chem Ranger, a U.S.-owned, Greek-operated, Marshall Island-flagged tanker ship, the U.S. Central Command said in a statement. Though the crew watched the missiles impact nearby water, the ship and its crew were not hurt or damaged, the statement continued.\n\nThe Houthis have connected their wave of attacks to the war on Gaza, saying they will continue to launch in protest of Israel’s campaign against Hamas.\n\nDan Lamothe and Alex Horton contributed to this report.\n\nBy: Karen DeYoung and Sammy Westfall\n\n7:47 PM: How Israel’s war in Gaza became a tangled crisis spanning the Middle East\n\nIsrael’s war in Gaza is at the center of a simmering regional crisis that has threatened to boil over in recent days, which have seen a string of strikes across the Middle East — some direct reverberations of Israel’s effort to root out Hamas.\n\nAs Israel targeted Hezbollah sites deep in southern Lebanon and the United States conducted a new round of strikes on what officials said were Houthi missile sites in Yemen, Iran launched strikes at what it said was an Israeli intelligence site in Iraq’s Kurdistan province and a militant site in Pakistan — prompting angry objections from both governments. Iran has also launched strikes into Syria, and its proxy groups in Iran and Syria have targeted U.S. troops there.\n\nAs strikes cascade, experts warn that a simple miscalculation could quickly spiral out of control.\n\n“They’re playing a very dangerous game — it’s chicken, basically,” Joost Hiltermann, a Middle East expert at the International Crisis Group, said this month of the various governments and militant groups increasingly enmeshed in regional tensions. “Any miscalculation, any miscommunication, any accidental strike could trigger a major escalation.”\n\nSome suggest that a regional conflict is already underway. Late last month, Israeli Defense Minister Yoav Gallant told a parliamentary committee that the country was defending itself in a “multi-arena” war that went beyond Gaza and the West Bank.\n\n“I say here in the most explicit way: Anyone who acts against us is a potential target. There is no immunity for anyone,” he said.\n\nHere are some of the flash points across the region.\n\nRead the full story\n\nBy: Adam Taylor\n\n6:55 PM: Netanyahu says Israel won’t end war until ‘complete victory’ is achieved\n\nIn an evening address to the nation, Prime Minister Benjamin Netanyahu pushed back on growing international calls for an end to the conflict: “We strive to achieve total victory,” he said. “This is not just a matter of hitting Hamas, this is not another round with Hamas — this is a complete victory.”\n\nHe said that ending the war without achieving Israel’s goals “will damage Israel’s security for generations” and “will send a message of weakness and encourage our enemies to think that they can defeat us, and then the next massacre will be only a matter of time.” So, Israel will continue to “fight with full force” until it achieves its goals.\n\nIsrael, he said, “must maintain security control over all territory west of the Jordan river.”\n\nLater in the day, U.S. State Department spokesperson Matthew Miller offered a different vision, saying there was “no way” to solve Israel’s long-term challenges and ensure lasting security “without the establishment of a Palestinian state.”\n\nTotal victory to Netanyahu also meant, the prime minister said, the elimination of “terrorist leaders,” destroying Hamas’s military and governing capabilities, returning hostages, and ensuring Gaza is demilitarized and “under Israel’s full security control, with Israeli control over everything that enters Gaza.”\n\n“We will not stop. We will not finish the war before returning our loved ones home; we will not finish the war before total victory,” Netanyahu said.\n\n“The US supports a two-state solution. It’s the only way to ensure security, dignity, and peace for both Israelis and Palestinians,” Sen. Elizabeth Warren (D-Mass.) later said in a post on X . “Netanyahu’s saying the quiet part out loud — it’s dangerous and directly contradicts US policy. Aid must be conditioned on working toward peace.”\n\nBy: Sammy Westfall\n\n5:57 PM: Why Gaza keeps losing communications\n\nBEIRUT — Israel’s war on Hamas has deprived people in Gaza of food, water, electricity and shelter.\n\nIt’s also disrupted communications. Gaza’s cellphone network had struggled before the conflict. Now, under Israeli bombardment and the mass displacement of Gazans, it’s failing as people are trying to connect with loved ones and secure resources.\n\nCommunications blackouts have also stymied aid organizations and emergency workers trying to coordinate with the local population and with each other. And for Gaza’s journalists, the blackouts are an impediment as they try to inform the world about suffering in the enclave.\n\nRead the full story\n\nBy: Mohamad El Chamaa and Júlia Ledur\n\n2:01 PM: Analysis from Karen DeYoung, Associate editor and senior national security correspondent\n\nIran’s strike on Pakistan was a “reckless attack” and “example of Iran’s destabilizing behavior in the region,” National Security Council spokesman John Kirby said Thursday. “While the United States does not have diplomatic relations with Iran, Pakistan is considered a U.S. partner in the region, with “major non-NATO ally” status. He said he was not aware of any “pre-notification that we received at all” from Pakistan before its retaliatory strike against Iran on Thursday.\n\n12:09 PM: Pakistan launches retaliatory attack on Iran in latest escalation of regional tensions\n\nISLAMABAD, Pakistan — Pakistan launched a series of retaliatory strikes Thursday on militants in Iran’s Sistan and Baluchistan province, its Foreign Ministry said , amid an increasingly tense situation in the Middle East that now appears to be straining relations between the nuclear-armed Pakistan and its neighbor.\n\nIranian state media reported that at least nine people, including three women and four children, were killed in the strikes, while Pakistani officials cited only the deaths of “a number of terrorists.”\n\nThe Pakistani attacks, carried out with “drones, rockets, loitering munitions and standoff weapons,” were launched in response to Iranian strikes inside Pakistan on Tuesday that killed two children, according to Pakistani officials. Both sides said they had targeted separatist militant groups that pose cross-border threats.\n\nWhile the Pakistan-Iran border has seen occasional outbreaks of violence in recent years, this week’s attacks came amid growing concerns over rising instability in the region following the launch of Israel’s war with Hamas militants, who are supported by Iran. Over the past week, the United States carried out several strikes against Iranian-backed Houthi militants in Yemen, who have been attacking shipping in the Red Sea; Iran, meanwhile, attacked targets in Iraq and Syria earlier this week.\n\nNoack reported from Kabul, George from Dubai, and Vinall from Melbourne, Australia.\n\nRead the full story\n\nBy: Shaiq Hussain, Rick Noack, Frances Vinall and Susannah George\n\n9:55 AM: Strike on displaced Gazans in Rafah kills 16 people\n\nRAFAH — A strike Thursday on a home in Rafah, in southern Gaza, that was housing displaced people killed at least 16 people, among them children and a pregnant woman, bystanders said at the scene.\n\nIn the aftermath, white body bags piled up outside of Najjar hospital, where the dead and injured were taken. Family members wept and prayed. The hospital had no available morgue to store the bodies. Countless Gazans have been hastily laid to rest in mass graves.\n\nTalat Barhoum, a doctor at Rafah’s Najjar Hospital, confirmed the death toll in a conversation with the Associated Press and said many more had been injured.\n\n“They were suffering from hunger, they were dying from hunger, and now they have also been hit,” Mahmoud Qassim, a relative of some of those killed, told the AP .\n\nThursday’s strike, the source of which The Post could not independently verify, left a scene of chaos, as neighbors climbed over the rubble to help the injured. Israel has repeatedly told civilians to flee to Rafah for their safety and about half of Gaza’s 2.2 million residents have crammed into the city on the Egyptian border — even as deadly Israeli strikes continue there.\n\nBerger reported from Jerusalem.\n\nBy: Loay Ayyoub and Miriam Berger\n\n8:33 AM: Hostage families accuse Netanyahu of scuttling releases\n\nSeveral relatives of hostages have this week publicly expressed their dissatisfaction with Prime Minister Benjamin Netanyahu and his government’s pace of progress toward releases.\n\nAt a news conference Wednesday, Liz Hirsh Naftali — whose grandniece, Abigail Edan , turned 4 in captivity before being freed Nov. 26 — rebuked Netanyahu for allowing more than 130 remaining hostages to languish in Hamas captivity in Gaza. Naftali also accused Netanyahu of scuttling deals that would have seen more hostages freed for the sake of advancing his political goals and wanting “to keep this war going to remain in office.”\n\nThe United States has a responsibility to get tough with Israel, Naftali added. “President Biden has been very clear that he and the U.S. government are friends of Israel and the Israeli people. But sometimes friends have to deliver hard messages,” she said.\n\nRuby Chen, the father of Israeli American hostage Itay Chen, told reporters at the event that he thought Netanyahu was “responsible, because it was on his watch what happened on Oct. 7, and he has the authority of bringing this to the finish line.”\n\nThe Israeli Prime Minister’s Office on Thursday denied the claim that Netanyahu was delaying hostage releases.\n\nIn Israel, the sister of slain hostage Itay Svirsky told Israeli Army Radio that she wished her brother had been killed on Oct. 7 rather than suffered as a hostage. “That way he would have been saved from 99 days of fear and death,” Merav Svirsky said.\n\nThe comments came as freed Israeli-Argentinian hostage Sharon Aloni Cunio told CNN on Wednesday that she was held in Nasser Hospital in Khan Younis “up until the end,” when she was freed along with her 3-year-old daughters in November in exchange for Palestinians held in Israel.\n\nCunio, 34, said she was held in one of three “exam rooms” 12 square feet in size, which she shared with about 10 other hostages. The Washington Post could not independently verify Cunio’s claims, and Netanyahu’s office declined to comment. Many hostages have said they were treated or held in hospitals, as well as mosques, schools and other civilian infrastructure.\n\nCunio’s husband, David, remains a hostage. The family was taken on Oct. 7 from their home in the Nir Oz kibbutz in southern Israel.\n\nBy: Abigail Hauslohner and Adela Suliman\n\n7:33 AM: Israeli troops withdraw from Nasser Hospital area in south, U.N. office says\n\nIsraeli forces withdrew from the vicinity of Nasser Hospital in Khan Younis on Wednesday, the U.N. Office for the Coordination of Humanitarian Affairs said , after heavy fighting and bombardment in the southern Gazan city this week that the office said destroyed residential buildings and a cemetery.\n\nAl Amal Hospital in Khan Younis was badly damaged by strikes in its vicinity on Tuesday, OCHA said. Artillery shelling near Nasser led to some munitions falling inside the hospital complex, but no casualties were reported, the office added.\n\nA Jordanian field hospital in the city was heavily damaged Wednesday, and one staff member and one patient were injured, the Jordanian army told local media. The Israel Defense Forces told the Times of Israel that the field hospital was not damaged.\n\nAs thousands of displaced civilians and patients fled Nasser Hospital this week, Doctors Without Borders said it was “extremely concerned” about the safety of its staff and patients there. On Tuesday night, Israeli forces bombed an area near Nasser Hospital without giving a prior evacuation order, the organization said, citing a surgeon working there. Thousands sheltering and receiving care “fled in a panic,” it said.\n\nEarlier in the day, the IDF accused Hamas of launching a rocket from within the hospital grounds, raising fears that an operation was imminent.\n\nNasser is the largest partially functional hospital remaining in the Gaza Strip, according to the United Nations. Thirteen of Gaza’s 36 hospitals are partially functional, two were minimally functioning, and 21 were not working at all, the World Health Organization said in December.\n\nBy: Loveday Morris, Sammy Westfall, Kareem Fahim and Frances Vinall\n\n6:24 AM: At least 10 Palestinians killed in two days of Israeli raids in the West Bank, health officials say\n\nJERUSALEM — Israeli forces stepped up raids across the occupied West Bank on Thursday, a day after Palestinian officials reported airstrikes in two refugee camps that they said killed at least nine people. At least one other Palestinian was killed by Israeli fire and 12 others were injured as of Thursday morning, the Palestine Red Crescent said.\n\nIsraeli military operations centered in the northern Tulkarm and Nur Shams refugee camps for a second day Thursday. Local media shared videos of Israeli bulldozers and tanks in torn-up streets, and reported on raids and clashes between Palestinian fighters and Israeli forces. A 27-year-old died of a gunshot wound in his abdomen in Tulkarm, the Ramallah-based Palestinian Health Ministry said.\n\nThe Israel Defense Forces told The Washington Post on Thursday that it, Shin Bet and border police were “continuing an ongoing counterterrorism operation in the Tulkarm Camp for over 35 hours” and that security forces were “continuing to operate in the city.” The IDF said it “exposed dozens of explosive devices” concealed under roads, located military equipment, struck an explosives laboratory and apprehended more than 15 people. In Nur Shams, there was “an activity to expose explosive devices using engineering tools” and exchanges of fire with Palestinian gunmen, the IDF said in a separate statement.\n\nElsewhere, Palestinians reported on Israeli raids in the village of Zawata outside Nablus, in Amari refugee camp near Ramallah and in Bani Naim village outside Hebron in the south. An IDF spokesperson told The Post that Israeli forces entered Amari to arrest a wanted person and Bani Naim for “a routine activity.” In both cases, a “violent riot was instigated” and “hits were identified,” said the spokesperson, who spoke on the condition of anonymity per military protocol.\n\nIsrael intensified raids and arrests across the West Bank after Hamas’s October attack, escalating intensive military campaigns that began in the spring of 2022. Israeli forces have killed more than 40 Palestinian fighters and civilians in the West Bank in 2024 alone, according to Palestinian health officials, and more than 320 people overall since Oct. 7 — a rate not seen in years.\n\nThe IDF has increasingly conducted lethal airstrikes in the West Bank since Oct. 7. On Wednesday, an Israeli airstrike killed four people in the Balata refugee camp near Nablus, according to the Palestinian Health Ministry. The IDF said the dead included the head of a local militant cell who “planned to carry out an imminent, large-scale, terrorist attack.” The IDF did not provide details on the alleged plans.\n\nHours later, an airstrike in Tulkarm killed at least five Palestinians, among them two 17-year-olds, according to the Palestinian Health Ministry. The IDF said the two had thrown explosives at its forces and one Israeli reservist was seriously injured by gunfire.\n\nThe Palestine Red Crescent said Israel prevented its ambulances from reaching Balata and Tulkarm on Wednesday. Israeli forces also fired toward its teams, injuring two ambulance drivers in Tulkarm, the group said.\n\nBy: Miriam Berger\n\n12:58 AM: U.S. Navy carries out new round of strikes against Houthis in Yemen\n\nThe U.S. Navy launched a new round of missile strikes against Houthi militants in Yemen, targeting about a dozen sites in a growing campaign meant to stifle repeated attacks on commercial shipping in the Red Sea, U.S. officials said late Wednesday.\n\nU.S. forces carried out the strikes on 14 missiles that the Houthis had “loaded to be fired,” military officials said in a statement released by U.S. Central Command. The missiles were on launch rails and “presented an imminent threat to merchant vessels and U.S. Navy ships and could have been fired at any time,” prompting U.S. forces to strike in self-defense, according to the statement.\n\nGen. Michael “Erik” Kurilla, the head of Central Command, said in the statement that the Houthis “continue to endanger international mariners and disrupt the commercial shipping lanes in the Southern Red and adjacent waterways.”\n\n“We will continue to take actions to protect the lives of innocent mariners and we will always protect our people,” Kurilla said. He called the militants “Houthi terrorists” in language that appeared to reflect the Biden administration’s decision, announced Wednesday, to put the militants on its list of specially designated terrorists .\n\nThe strikes were carried out with Tomahawk missiles, two defense officials said, speaking on condition of anonymity because of the sensitivity of the issue. At least one warship and one submarine were involved, the officials said.\n\nRead the full story\n\nBy: Dan Lamothe')"
    AI_generated_questions, relevant_articles, out = q2a_workflow(article, query, 10)
    save_to_file([query, article, AI_generated_questions, relevant_articles, out])
                                                                  

    
