# -*- coding: utf-8 -*-
# """skool_partneredyoutube_01_fetch_posts.ipynb
#
# Automatically generated by Colab.
#
# Original file is located at
#   https://colab.research.google.com/drive/10mianE-19RDI3sUOdYtNToZd-qfBX38P
# """

import os
import praw
import google.generativeai as genai
from datetime import datetime, timedelta
# import chromadb
# from chromadb.config import Settings
# from chromadb.utils import embedding_functions
# from sentence_transformers import SentenceTransformer
# from google.colab import drive
# import json

# Mount Google Drive
# drive.mount('/content/drive')

# Configure paths
SUBREDDIT_SOURCE = 'PartneredYoutube'
SUBREDDIT_DESTINATION = 'YoutubeCreatorHub'
# BASE_PATH = '/content/drive/MyDrive/vector_store'
# SUBREDDIT_PATH = os.path.join(BASE_PATH, SUBREDDIT_NAME)
# CHROMA_PERSIST_DIRECTORY = os.path.join(SUBREDDIT_PATH, 'chroma_db')
# JSON_STORAGE_PATH = os.path.join(SUBREDDIT_PATH, f'{SUBREDDIT_NAME}_digest_data.json')

# Create necessary directories
# os.makedirs(CHROMA_PERSIST_DIRECTORY, exist_ok=True)

# Configure Reddit API
reddit = praw.Reddit(
    client_id=os.environ['REDDIT_CLIENT_ID'],
    client_secret=os.environ['REDDIT_CLIENT_SECRET'],
    user_agent=os.environ['REDDIT_USER_AGENT'],
    username=os.environ['REDDIT_USERNAME'],
    password=os.environ['REDDIT_PASSWORD']
)

# Configure Gemini AI
genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('models/gemini-1.5-pro-latest')

# Configure Chroma
# chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIRECTORY)
# sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
# collection = chroma_client.get_or_create_collection(name=f"{SUBREDDIT_NAME}_posts", embedding_function=sentence_transformer_ef)

def get_recent_posts(subreddit_name, time_filter='day'):
    subreddit = reddit.subreddit(subreddit_name)
    posts = []
    for post in subreddit.top(time_filter=time_filter, limit=None):
        posts.append({
            'id': post.id,
            'title': post.title,
            'url': post.url,
            'score': post.score,
            'num_comments': post.num_comments,
            'body': post.selftext
        })
    return posts

def get_top_comments(post_id, limit=5):
    submission = reddit.submission(id=post_id)
    submission.comment_sort = 'top'
    submission.comments.replace_more(limit=0)
    return [comment.body for comment in submission.comments[:limit]]

def generate_digest(posts):
    content = f"{SUBREDDIT_DESTINATION} - Daily Summary for r/{SUBREDDIT_SOURCE}\n\n"
    for post in posts[:10]:  # Summarize top 10 posts
        content += f"Title: {post['title']}\n"
        content += f"Score: {post['score']}, Comments: {post['num_comments']}\n"
        content += f"URL: {post['url']}\n\n"
        if post['body']:
            content += f"Content: {post['body'][:500]}...\n\n"

        top_comments = get_top_comments(post['id'])
        if top_comments:
            content += "Top Comments:\n"
            for comment in top_comments:
                content += f"- {comment[:100]}...\n"
        content += "\n---\n\n"

    prompt = f"""
    Summarize the following YouTube creator-related content into a concise, educational daily digest. Structure your response as follows:

    1. Brief introduction (2-3 sentences max)

    2. Top Discussions (Choose 3-4 most relevant):
      - Categorize each (e.g., Monetization, Content Strategy, Platform Policies)
      - Summarize the discussion (2-3 sentences)
      - Provide a "Key Takeaway" or "Action Item" (1 sentence)
      - Include relevant statistics or data points if available

    3. Trend Watch:
      - Identify an emerging topic or shift in the creator landscape (1-2 sentences)

    4. Creator Spotlight:
      - Highlight a success story or effective strategy from the community (2-3 sentences)

    5. Resource of the Day:
      - Recommend a tool, article, or video relevant to creators (1-2 sentences)

    6. Challenge of the Week:
      - Suggest a task or experiment for creators to try (1-2 sentences)

    7. Did You Know?
      - Explain a YouTube feature or policy (1-2 sentences)

    8. Questions to Consider:
      - Pose 2-3 reflective questions for creators about their strategies

    Aim for a clear, concise, and actionable digest that provides immediate value to YouTube creators while encouraging further learning and experimentation. Use bullet points for readability. Keep the entire digest under 500 words.
    \n\n{content}
    """
    response = model.generate_content(prompt)
    return response.text

def post_digest(digest):
    subreddit = reddit.subreddit(SUBREDDIT_DESTINATION)
    title = f"YouTube Creator Digest - r/{SUBREDDIT_SOURCE} - {datetime.now().strftime('%Y-%m-%d')}"
    subreddit.submit(title, selftext=digest)

# def save_to_vector_store(posts, digest):
#     for post in posts:
#         collection.add(
#             documents=[post['title'] + "\n" + post['body']],
#             metadatas=[{
#                 'id': post['id'],
#                 'title': post['title'],
#                 'url': post['url'],
#                 'score': post['score'],
#                 'num_comments': post['num_comments'],
#                 'date': datetime.now().strftime('%Y-%m-%d')
#             }],
#             ids=[post['id']]
#         )

#     # Save digest
#     digest_id = f"digest_{datetime.now().strftime('%Y-%m-%d')}"
#     collection.add(
#         documents=[digest],
#         metadatas=[{'type': 'digest', 'date': datetime.now().strftime('%Y-%m-%d')}],
#         ids=[digest_id]
#     )

# def save_to_json(posts, digest):
#     date = datetime.now().strftime('%Y-%m-%d')
#     data = {
#         'date': date,
#         'posts': posts,
#         'digest': digest
#     }

#     if os.path.exists(JSON_STORAGE_PATH):
#         with open(JSON_STORAGE_PATH, 'r') as f:
#             existing_data = json.load(f)
#     else:
#         existing_data = []

#     existing_data.append(data)

#     with open(JSON_STORAGE_PATH, 'w') as f:
#         json.dump(existing_data, f, indent=2)

def main():
    posts = get_recent_posts(SUBREDDIT_SOURCE)
    digest = generate_digest(posts)
    post_digest(digest)
    # save_to_vector_store(posts, digest)
    # save_to_json(posts, digest)
    print(f"Daily digest from r/{SUBREDDIT_SOURCE} to r/{SUBREDDIT_DESTINATION} posted successfully!")

if __name__ == "__main__":
    main()

import praw
import time
import os

# Configure Reddit API
reddit = praw.Reddit(
    client_id=os.environ['REDDIT_CLIENT_ID'],
    client_secret=os.environ['REDDIT_CLIENT_SECRET'],
    user_agent=os.environ['REDDIT_USER_AGENT'],
    username=os.environ['REDDIT_USERNAME'],
    password=os.environ['REDDIT_PASSWORD']
)

def remove_low_vote_comments():
    # Get the authenticated user's comments
    user = reddit.user.me()

    # Counter for removed comments
    removed_count = 0

    # Iterate through user's comments
    for comment in user.comments.new(limit=None):
        # Check if comment has less than one vote
        if comment.score < 1:
            try:
                # Delete the comment
                comment.delete()
                print(f"Comment score: {comment.score}")  # Print first 50 characters of comment
                print(f"Removed comment: {comment.body[:50]}...")  # Print first 50 characters of comment
                removed_count += 1

                # Sleep to avoid hitting rate limits
                time.sleep(2)
            except Exception as e:
                print(f"Error removing comment: {comment.body[:50]}...")
                print(f"Error message: {str(e)}")

    print(f"Total comments removed: {removed_count}")

if __name__ == "__main__":
    remove_low_vote_comments()
