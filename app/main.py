import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

from app import create_app
from app.services.recommendations_service import get_recommendations

# Initialize the Flask app
app = create_app()

def main():
    user_query = "I want to go for the sucba in tell me the best place"
    response = get_recommendations(user_query)
    print("Recommendations for the query:")
    for recommendation in response:
        if isinstance(recommendation, dict):
            print(f"Experience ID: {recommendation.get('id', 'N/A')}")
            print(f"Name: {recommendation.get('name', 'N/A')}")
            print(f"Location: {recommendation.get('location', 'N/A')}")
        else:
            print(recommendation)
        print("-" * 40)

if __name__ == "__main__":
    main()
    app.run(debug=True)
