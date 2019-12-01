from bs4 import BeautifulSoup
from urllib.request import urlopen, urlretrieve, Request
import urllib.parse as urlparse
import requests, shutil, os, img2pdf
from tqdm import tqdm

urlinput = []
urlform = ["https://www.webtoons.com/en/fantasy/refundhighschool/ep-","/viewer?title_no=1360&episode_no="]
for i in range(1,103):
    urlinput.append(urlform[0]+str(i)+urlform[1]+str(i))

doctitle = "rhs 1-103 test"
urls = []
filenames = []

if not os.path.exists(doctitle):
    os.makedirs(doctitle)

print("Step 1: Getting image urls")
for url in tqdm(urlinput, unit="links", ncols=100):
    soup = BeautifulSoup(urlopen(url).read(),features="html.parser")
    parser = urlparse.parse_qs(urlparse.urlparse(url).query)

    for i in soup.find_all("div"):
        if i.get("id"):
            if i.get("id") == "_imageList":
                for a in i.find_all("img"):
                    urls.append(a.get("data-url"))
                    #print("getting: "+str(len(urls)))

    with open(doctitle+"/"+doctitle+".txt","a+") as file:
        for i in urls:
            if urls.index(i) == len(urls)-1:
                file.write(i)
            else:
                file.write(i+"\n")

os.system("cls")
print("Step 2: Saving files")
for i in tqdm(urls, unit="images", ncols=100):
    index = urls.index(i)
    filename = doctitle+"/"+doctitle+"-"+str(index)+".jpg"
    try:
        r = requests.get(i, stream=True, headers={'User-agent': 'Mozilla/5.0', "Referer": urlinput[0]})
        if r.status_code == 200:
            with open(filename, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
    except Exception as error:
        print("Error saving "+filename)
        print("Error: "+error)
    else:
        filenames.append(filename)
        #print("saved: "+str(len(filenames)))

print("Saving pdf...")
with open(doctitle+"/"+doctitle+".pdf", "wb") as f:
    f.write(img2pdf.convert(filenames))
print("Successfully saved pdf! Press any key to exit.")
os.system("pause >nul")
