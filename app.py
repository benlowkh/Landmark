from flickr import FlickrAPI
from flask import Flask, jsonify, render_template
import requests
import json
import httplib, urllib, base64
import random
from rauth import OAuth1Service

app = Flask(__name__)
app.config["DEBUG"] = True  # Only include this while you are testing your app

@app.route("/")
def hello():
    return render_template("search.html")

@app.route("/maps/<loc1>/<loc2>")
def maps(loc1,loc2):
	bing_maps_key = "PUT_KEY_HERE"
	r = requests.get('http://dev.virtualearth.net/REST/V1/Routes/Driving?wp.0='+loc1+'&wp.1='+loc2+'&key='+bing_maps_key)
	r_dict = r.json()
	route_obj = r_dict["resourceSets"][0]["resources"][0]
	route_dir = route_obj["routeLegs"][0]["itineraryItems"]

	directions_list = []
	i = -1
	for r_instr in route_dir:
		i += 1
		dir_obj = {}
		r_text = r_instr["instruction"]["text"]
		dir_obj["coords"] = "("+str(r_instr["maneuverPoint"]["coordinates"][0]) + ", "+str(r_instr["maneuverPoint"]["coordinates"][1])+")"

		# get hints
		try:
			dir_obj["hint"] = r_instr["hints"][1]["text"]+"."
		except:
			dir_obj["hint"] = ""

		# FLICKR
		api_key = "PUT_FLICKR_KEY_HERE"
		api_secret = "PUT_FLICKR_SECRET_HERE"

		flickr = FlickrAPI(api_key, api_secret, '/')
		auth_props = flickr.get_authentication_tokens()
		auth_url = auth_props['auth_url']

		oauth_token = auth_props['oauth_token']
		oauth_token_secret = auth_props['oauth_token_secret']

		photo_json = flickr.get('flickr.photos.search', params={'api_key':api_key, 'lat': r_instr["maneuverPoint"]["coordinates"][0], 'lon': r_instr["maneuverPoint"]["coordinates"][1], 'radius': '0.01'})
		photos = photo_json['photos']['photo']
		photo = random.choice(photos)
		flickr_image_url = 'https://farm' + str(photo['farm']) + '.staticflickr.com/' + str(photo['server']) + '/' + str(photo['id']) + '_' + photo['secret'] + '.jpg'

		# PROJECT OXFORD 
		oxford_key = "PUT_KEY_HERE"

		headers = {
		    # Request headers
		    'Content-Type': 'application/json',
		    'Ocp-Apim-Subscription-Key': oxford_key,
		}

		params = urllib.urlencode({
		    # Request parameters
		    'visualFeatures': 'All',
		})


		try:
		    conn = httplib.HTTPSConnection('api.projectoxford.ai')
		    conn.request("POST", "/vision/v1/analyses?%s" % params, '{ "Url":"'+flickr_image_url+'"}',headers)
		    ox_response = conn.getresponse()
		    ox_data = ox_response.read()
		    ox_json = json.loads(ox_data)
		    #print(ox_data)
		    conn.close()
		except Exception as e:
		    print("[Errno {0}] {1}".format(e.errno, e.strerror))

		# combine directions + descriptions
		try:
			if ox_json["categories"][0]["name"] != "others_":
				r_text = r_text + " near this " + ox_json["categories"][0]["name"]
				#print flickr_image_url
			else:
				pass
			
		except:
			#print "program failed because of oxford. IMAGE URL \n"
			#print flickr_image_url
			#print "OXFORD RESPONSE: \n"
			#print ox_data
			pass

		r_text = r_text +". "
		r_text = r_text.replace("_"," ")
		r_text = r_text.replace("abstract","landmark")
		r_text = r_text.replace("outdoor","outdoor area")
		r_text = r_text.replace(" .",".")
		print r_text
		dir_obj["r_text"] = r_text
		dir_obj["url"] = flickr_image_url
		directions_list.append(dir_obj)

	#return json.dumps(directions_list)
	return render_template("maps.html",my_list = directions_list)

@app.route("/search")
def search():
	return render_template("search.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0")
