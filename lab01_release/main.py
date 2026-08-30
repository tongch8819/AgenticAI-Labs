from typing import Dict, List
from autogen import ConversableAgent
import sys
import os

def fetch_restaurant_data(restaurant_name: str) -> Dict[str, List[str]]:
    # This function takes in a restaurant name and returns the reviews for that restaurant. 
    # The output should be a dictionary with the key being the restaurant name and the value being a list of reviews for that restaurant.
    # The "data fetch agent" should have access to this function signature, and it should be able to suggest this as a function call. 
    # Example:
    # > fetch_restaurant_data("Applebee's")
    # {"Applebee's": ["The food at Applebee's was average, with nothing particularly standing out.", ...]}
    # pass
    reviews = []   # have multiple reviews
    src_file_path = os.path.join(os.path.dirname(__file__), 'restaurant-data.txt')
    with open(src_file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # each line has format: [restaurant_name]. review_text
            name, review = line.split(". ", 1)
            if name.strip().lower() == restaurant_name.strip().lower():
                reviews.append(review.strip())
    return {restaurant_name: reviews}

def calculate_overall_score(restaurant_name: str, food_scores: List[int], customer_service_scores: List[int]) -> Dict[str, float]:
    # TODO
    # This function takes in a restaurant name, a list of food scores from 1-5, and a list of customer service scores from 1-5
    # The output should be a score between 0 and 10, which is computed as the following:
    # SUM(sqrt(food_scores[i]**2 * customer_service_scores[i]) * 1/(N * sqrt(125)) * 10
    # The above formula is a geometric mean of the scores, which penalizes food quality more than customer service. 
    # Example:
    # > calculate_overall_score("Applebee's", [1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
    # {"Applebee's": 5.048}
    # NOTE: be sure to that the score includes AT LEAST 3  decimal places. The public tests will only read scores that have 
    # at least 3 decimal places.
    # pass
    n = len(food_scores)
    if n == 0:
        return {restaurant_name: 0.0}
    total_score = sum((food_scores[i] ** 2 * customer_service_scores[i]) ** 0.5 for i in range(n))
    overall_score = (total_score / (n * (125 ** 0.5))) * 10
    res = {restaurant_name: round(overall_score, 3)}
    print(res)
    return res

def get_data_fetch_agent_prompt(restaurant_query: str) -> str:
    # TODO
    # It may help to organize messages/prompts within a function which returns a string. 
    # For example, you could use this function to return a prompt for the data fetch agent 
    # to use to fetch reviews for a specific restaurant.
    pass

# TODO: feel free to write as many additional functions as you'd like.

# Do not modify the signature of the "main" function.
def main(user_query: str):
    entrypoint_agent_system_message = "You are the supervisor coordinating restaurant review tasks." # TODO
    # example LLM config for the entrypoint agent
    # llm_config = {"config_list": [{"model": "gpt-4o-mini", "api_key": os.environ.get("OPENAI_API_KEY")}]}
    llm_config = {"config_list": [
    #     {
    #     # "model": "qwen/qwen3.8-27b",
    #     "model" : "qwen/qwen3.6-27b",
    #     "base_url": "https://api.groq.com/openai/v1",
    #     "api_key": os.environ.get("GROQ_API_KEY")
    # }
    {
        "model": "gemini-3.6-flash",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key": os.environ.get("GEMINI_API_KEY")
    }
    
        ]}
    # the main entrypoint/supervisor agent
    entrypoint_agent = ConversableAgent(
        name="entrypoint_agent", 
        system_message=entrypoint_agent_system_message, 
        llm_config=llm_config,
        human_input_mode="NEVER"
    )
    # entrypoint_agent.register_for_llm(name="fetch_restaurant_data", description="Fetches the reviews for a specific restaurant.")(fetch_restaurant_data)
    # entrypoint_agent.register_for_execution(name="fetch_restaurant_data")(fetch_restaurant_data)

    # TODO
    # Create more agents here. 
    
    # Task 1: Create the data fetch agent
    data_fetch_agent = ConversableAgent(
        name="data_fetch_agent",
        system_message="You extract the restaurant name from the user's query and call fetch_restaurant_data. "
            "Once you receive the tool output, your final reply MUST ONLY be the JSON dictionary of the fetched data. "
            "Do not summarize or alter the reviews.",
        llm_config=llm_config,
        human_input_mode="NEVER"
    )

    
    # Task 2: review analyzer
    review_analyzer_system_message = """You are an expert review analyzer.
Your job is to analyze restaurant reviews and extract two integer scores (1-5) for each review:
1. food_score: based on adjectives describing the food quality.
2. customer_service_score: based on adjectives describing customer service.

Use EXACTLY the following mapping for adjective keywords:
- Score 1: awful, horrible, disgusting
- Score 2: bad, unpleasant, offensive
- Score 3: average, uninspiring, forgettable
- Score 4: good, enjoyable, satisfying
- Score 5: awesome, incredible, amazing

For each review:
- Find the food keyword -> extract food_score
- Find the service keyword -> extract customer_service_score

Output the extracted scores clearly. When finished, conclude with the lists:
food_scores: [score1, score2, ...]
customer_service_scores: [score1, score2, ...]
"""
    review_analyzer_agent = ConversableAgent(
        name="review_analyzer_agent",
        system_message=review_analyzer_system_message,
        llm_config=llm_config,
        human_input_mode="NEVER"
    )
        
    # Task 3: scoring agent
    scoring_agent_system_message = """You are a scoring agent.
Your job is to take the extracted food_scores and customer_service_scores for the restaurant and call the calculate_overall_score function with:
- restaurant_name: name of the restaurant
- food_scores: list of integer food scores
- customer_service_scores: list of integer customer service scores
"""
    scoring_agent = ConversableAgent(
        name="scoring_agent",
        system_message=scoring_agent_system_message,
        llm_config=llm_config,
        human_input_mode="NEVER"
    )
    
    
    data_fetch_agent.register_for_llm(name="fetch_restaurant_data", description="Fetches the reviews for a specific restaurant.")(fetch_restaurant_data)
    entrypoint_agent.register_for_execution(name="fetch_restaurant_data")(fetch_restaurant_data)
    scoring_agent.register_for_llm(name="calculate_overall_score", description="Calculates the overall score for a restaurant based on food and customer service scores.")(calculate_overall_score)
    entrypoint_agent.register_for_execution(name="calculate_overall_score")(calculate_overall_score)
    
    # TODO
    # Fill in the argument to `initiate_chats` below, calling the correct agents sequentially.
    # If you decide to use another conversation pattern, feel free to disregard this code.
    
    # Uncomment once you initiate the chat with at least one agent.
    chat_results = entrypoint_agent.initiate_chats([
        # Task 1: Fetch reviews
        {
            "recipient" : data_fetch_agent,
            "message" : user_query,
            "max_turns" : 2,
            "summary_method" : "last_msg"
        },
        # Task 2: Analyze reviews
        {
            "recipient" : review_analyzer_agent,
            "message" : "Analyze all fetched reviews and extract food_score and customer_service_score for each review based on the keywords.",
            "max_turns" : 1,
            "summary_method" : "last_msg"
        },
        # Task 3: Scoring agent
        {
            "recipient" : scoring_agent,
            "message": "Call calculate_overall_score using the extracted scores and restaurant name.",
            "max_turns" : 1,
            "summary_method" : "last_msg"
        }
    ])
    # print("\n--- Summary Result ---")
    # print(chat_results[0].summary)
    # print(chat_results[1].summary)
    # print(chat_results[2].summary)

# DO NOT modify this code below.
if __name__ == "__main__":
    assert len(sys.argv) > 1, "Please ensure you include a query for some restaurant when executing main."
    main(sys.argv[1])