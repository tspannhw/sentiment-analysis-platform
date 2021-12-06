import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
nltk.download([
  "names",
  "stopwords",
  "state_union",
  "twitter_samples",
  "movie_reviews",
  "averaged_perceptron_tagger",
  "vader_lexicon",
  "punkt",
])
sia = SentimentIntensityAnalyzer()
# sia.polarity_scores("Wow, NLTK is really powerful!")