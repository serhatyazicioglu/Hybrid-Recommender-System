#############################################
# Adım 1: Verinin Hazırlanması
#############################################
import pandas as pd

pd.set_option('display.max_columns', 20)


def create_user_movie_df():
    import pandas as pd
    movie = pd.read_csv('datasets/movie.csv', low_memory=True)
    rating = pd.read_csv('datasets/rating.csv', low_memory=True)
    df = movie.merge(rating, how="left", on="movieId")
    df['title'] = df.title.str.replace('(\(\d\d\d\d\))', '')
    df['title'] = df['title'].apply(lambda x: x.strip())
    a = pd.DataFrame(df["title"].value_counts())
    rare_movies = a[a["title"] <= 1000].index
    common_movies = df[~df["title"].isin(rare_movies)]
    user_movie_df = common_movies.pivot_table(index=["userId"], columns=["title"], values="rating")
    return user_movie_df


user_movie_df = create_user_movie_df()

user_movie_df.shape
user_movie_df.head()

user_id = 108170

#############################################
# Adım 2: Öneri yapılacak kullanıcının izlediği filmlerin belirlenmesi
#############################################

user_df = user_movie_df[user_movie_df.index == user_id]

movies_watched = user_df.columns[user_df.notna().any()].tolist()

#############################################
# Adım 3: Aynı filmleri izleyen diğer kullanıcıların verisine ve id'lerine erişmek
#############################################

movies_watched_df = user_movie_df[movies_watched]
movies_watched_df.head()

user_movies_count = movies_watched_df.T.notnull().sum()
user_movies_count = user_movies_count.reset_index()
user_movies_count.columns = ["userId", "movie_count"]

perc = len(movies_watched) * 60 / 100
user_movies_count[user_movies_count["movie_count"] > perc].sort_values("movie_count", ascending=False)

users_same_movies = user_movies_count[user_movies_count["movie_count"] > perc]["userId"]

#############################################
# Adım 4: Öneri yapılacak kullanıcı ile en benzer kullanıcıların belirlenmesi
#############################################

final_df = pd.concat([movies_watched_df[movies_watched_df.index.isin(users_same_movies.index)],
                      user_df[movies_watched]])

corr_df = final_df.T.corr().unstack().sort_values().drop_duplicates()
corr_df = pd.DataFrame(corr_df, columns=["corr"])
corr_df.index.names = ['user_id_1', 'user_id_2']
corr_df = corr_df.reset_index()
corr_df.head()

top_users = corr_df[(corr_df["user_id_1"] == user_id) & (corr_df["corr"] >= 0.65)][
    ["user_id_2", "corr"]].reset_index(drop=True)

top_users = top_users.sort_values(by='corr', ascending=False)

top_users.rename(columns={"user_id_2": "userId"}, inplace=True)

rating = pd.read_csv('datasets/rating.csv')
top_users_ratings = top_users.merge(rating[["userId", "movieId", "rating"]], how='inner')
top_users_ratings
top_users_ratings.shape

#############################################
# Adım 5: Weighted rating'lerin  hesaplanması
#############################################

top_users_ratings["weighted_rating"] = top_users_ratings["corr"] * top_users_ratings["rating"]
top_users_ratings.head()

#############################################
# Adım 6: Weighted average recommendation score'un hesaplanması
#############################################

temp = top_users_ratings.groupby('movieId').sum()[['corr', 'weighted_rating']]
temp.columns = ["sum_corr", "sum_weighted_rating"]
temp.head()

recommendation_df = pd.DataFrame()
recommendation_df['weighted_average_recommendation_score'] = temp['sum_weighted_rating'] / temp['sum_corr']
recommendation_df['movieId'] = temp.index
recommendation_df = recommendation_df.sort_values(by='weighted_average_recommendation_score', ascending=False)
recommendation_df.head(10)

movie = pd.read_csv("datasets/movie.csv")
movie_user = movie.loc[movie['movieId'].isin(recommendation_df.head(10)['movieId'].head())]['title']
movie_user.head()
movie_user[:5]

#############################################
# Adım 7: İzlediği filmlerden en son en yüksek puan verdiği filmin adına göre item-based öneri yapınız.
# 5 öneri user-based 5 öneri item-based olacak şekilde 10 öneri yapınız.
#############################################

pd.set_option('display.max_columns', None)

movie = pd.read_csv('datasets/movie.csv')
rating = pd.read_csv('datasets/rating.csv')
df = movie.merge(rating, how="left", on="movieId")
df.head()


# title

df['year_movie'] = df.title.str.extract('(\(\d\d\d\d\))', expand=False)
df['year_movie'] = df.year_movie.str.extract('(\d\d\d\d)', expand=False)
df['title'] = df.title.str.replace('(\(\d\d\d\d\))', '')
df['title'] = df['title'].apply(lambda x: x.strip())

# genres

df["genre"] = df["genres"].apply(lambda x: x.split("|")[0])
df.drop("genres", inplace=True, axis=1)
df.head()

# timestamp

df["timestamp"] = pd.to_datetime(df["timestamp"], format='%Y-%m-%d')
df["year"] = df["timestamp"].dt.year
df["month"] = df["timestamp"].dt.month
df["day"] = df["timestamp"].dt.day
df.head()

# User Movie Df'inin Oluşturulması

df["title"].nunique()
a = pd.DataFrame(df["title"].value_counts())

rare_movies = a[a["title"] <= 1000].index
common_movies = df[~df["title"].isin(rare_movies)]

common_movies["title"].nunique()

item_movie_df = common_movies.pivot_table(index=["userId"], columns=["title"], values="rating")

# Korelasyona Dayalı Item-Based Film Önerilerinin Yapılması

movieId = \
    rating[(rating["rating"] == 5.0) & (rating["userId"] == user_id)].sort_values(by="timestamp", ascending=False)[
        "movieId"][0:1].values[0]

movie_title = movie[movie["movieId"] == movieId]["title"].str.replace('(\(\d\d\d\d\))', '').str.strip().values[0]

movie = item_movie_df[movie_title]
movie_item = item_movie_df.corrwith(movie).sort_values(ascending=False)
item_movie_df[1:6].index

# user-based 5 öneri ve item-based 5 öneriyi bir araya getiriniz.

data_user_item = pd.DataFrame()
data_user_item["user_recommendations"] = movie_user[:5].values.tolist()
data_user_item["item_recommendations"] = movie_item[:5].index