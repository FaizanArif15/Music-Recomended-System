from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pickle
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

app = FastAPI()

# Serve the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

class CustomJinja2Templates(Jinja2Templates):
    def __init__(self, directory: str):
        super().__init__(directory)
        self.env.globals.update(zip=zip)

templates = CustomJinja2Templates(directory="templates")

CLIENT_ID = "Enter Your Client ID"
CLIENT_SECRET = "Enter Your Client Secret"


client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

music = pickle.load(open('df.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

def get_song_album_cover_url(song_name, artist_name):
    search_query = f"track:{song_name} artist:{artist_name}"
    results = sp.search(q=search_query, type="track")

    if results and results["tracks"]["items"]:
        track = results["tracks"]["items"][0]
        album_cover_url = track["album"]["images"][0]["url"]
        return album_cover_url
    else:
        return "/static/social.png"

def recommend(song):
    index = music[music['song'] == song].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_music_names = []
    recommended_music_posters = []
    for i in distances[1:6]:
        artist = music.iloc[i[0]].artist
        recommended_music_posters.append(get_song_album_cover_url(music.iloc[i[0]].song, artist))
        recommended_music_names.append(music.iloc[i[0]].song)

    return recommended_music_names, recommended_music_posters

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    music_list = music['song'].values
    return templates.TemplateResponse("index.html", {"request": request, "music_list": music_list})

@app.post("/recommend", response_class=JSONResponse)
async def show_recommendation(selected_song: str = Form(...)):
    recommended_music_names, recommended_music_posters = recommend(selected_song)
    return JSONResponse({"names": recommended_music_names, "posters": recommended_music_posters})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
