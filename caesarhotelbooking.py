# -*- coding: utf-8 -*-
import itertools
import re
import sys
import requests
import json
from bs4 import BeautifulSoup
from tqdm import tqdm

class CaesarHotelBooking:
    def __init__(self) -> None:
        pass

    @classmethod
    def create_url(self,city,num_of_adults,num_of_rooms,num_of_children,checkin_date,checkout_date,purpose,page_num=1):
        # pages go in 25 intervals
        self.checkin_date = checkin_date
        self.checkout_date = checkout_date
        self.city = city
        page_num_offset = (page_num-1) * 25
        url = f"https://www.booking.com/searchresults.en-gb.html?ss={city}&label=gen173nr-1FCAEoggI46AdIM1gEaGyIAQGYATG4AQfIAQzYAQHoAQH4AQKIAgGoAgO4AvTIm_IFwAIB&aid=304142&lang=en-gb&sb=1&src_elem=sb&src=searchresults&checkin={checkin_date}&checkout={checkout_date}&group_adults={num_of_adults}&no_rooms={num_of_rooms}&group_children={num_of_children}&sb_travel_purpose={purpose}&offset={page_num_offset}"
        return url
    @staticmethod
    def find_indices(list_to_check, item_to_find):
        indices = []
        for idx, value in enumerate(list_to_check):
            if value == item_to_find:
                indices.append(idx)
        return indices


    @classmethod
    def caesar_get_hotel_info(self,url):
        bookings = []
        assumed_vat_percentage = 0.2
        rating_regex = re.compile(r"^(?=.*?\d)\d*[.,]?\d*$")
        headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9'}
        response=requests.get(url,headers=headers)
        soup=BeautifulSoup(response.content,'lxml')

        title = [titl.text for titl in soup.find_all('div', attrs={'data-testid': 'title'})]
        city_list  = [self.city.capitalize() for vatind in range(len(title))]
        
        address = [addr.text for addr in soup.find_all('span', attrs={'data-testid': 'address'})]
        price = [float(price.text.replace("£","").replace(",","").replace("US$","")) for price in soup.find_all('span', attrs={'data-testid': 'price-and-discounted-price'})]
        assumed_vat = [f"{assumed_vat_percentage *100}%" for vatind in range(len(price))]
        checkin = [self.checkin_date for checkin in range(len(title))]
        checkout = [self.checkout_date for checkout in range(len(title))]
        assumed_final_price = [pr * (1 +assumed_vat_percentage ) for pr in price]
        booking = [xnights.text for xnights in soup.find_all('div', attrs={'data-testid': 'price-for-x-nights'})]
        room = [recounit.find("span").text for recounit in soup.find_all('div', attrs={'data-testid': 'recommended-units'})]
        #location = [recounit.find("a").get("href") for recounit in soup.find_all('h3',href=True)]
        location = []
        for recounit in soup.find_all('h3'):
            res = recounit.find("a")
            if res:
                location.append(res.get("href"))
        distance = [dist.text for dist in soup.find_all('span', attrs={'data-testid': 'distance'})]
        reviews = [rev.text for rev in soup.find_all('div', attrs={'class': 'd8eab2cf7f c90c0a70d3 db63693c62'})]
        rating = [float(rate.text) for rate in soup.select("[aria-label]") if rating_regex.match(rate.text) and "." in rate.text]
        

        for bookingind in range(len(title)):
            booking_info = {}
            try:
                city_json = {'city':city_list[bookingind]}
                booking_info.update(city_json)
            except IndexError as ex:
                pass
            try:
                title_json = {'title':title[bookingind]}
                booking_info.update(title_json)
            except IndexError as ex:
                continue
            try:
                checkin_date_json = {'checkin_date':checkin[bookingind]}
                booking_info.update(checkin_date_json)
            except IndexError as ex:
                pass
            try:
                checkout_date_json = {'checkout_date':checkout[bookingind]}
                booking_info.update(checkout_date_json)
            except IndexError as ex:
                pass
            try:
                address_json = {'address':address[bookingind]}
                booking_info.update(address_json)
            except IndexError as ex:
                pass
            try:
                price_json = {'price':price[bookingind]}
                booking_info.update(price_json)
            except IndexError as ex:
                pass
            try:
                assumed_vat_json = {'assumed_vat':assumed_vat[bookingind]}
                booking_info.update(assumed_vat_json)
            except IndexError as ex:
                pass
            try:
                assumed_final_price_json = {'assumed_final_price':assumed_final_price[bookingind]}
                booking_info.update(assumed_final_price_json)
            except IndexError as ex:
                pass
            try:
                booking_json = {'booking':booking[bookingind]}
                booking_info.update(booking_json)
            except IndexError as ex:
                pass
            try:
                distance_json = {'distance':distance[bookingind]}
                booking_info.update(distance_json)
            except IndexError as ex:
                pass
            try:
                reviews_json = {'reviews':reviews[bookingind]}
                booking_info.update(reviews_json)
            except IndexError as ex:
                pass
            try:
                room_json = {'room':room[bookingind]}
                booking_info.update(room_json)
            except IndexError as ex:
                pass
            try:
                rating_json = {'rating':rating[bookingind]}
                booking_info.update(rating_json)
            except IndexError as ex:
                pass
            try:
                location_json = {'location':location[bookingind]}
                booking_info.update(location_json)
            except IndexError as ex:
                pass
            bookings.append(booking_info)

        return bookings
def store_lower_than_3000(city,range):
    def condition(dic):
        ''' Define your own condition here'''
        try:
            price = dic['assumed_final_price']
            return price <= range
        except KeyError as kex:
            return False
    with open(f"{city.lower()}_bookings.json","r") as f:
        bookings = json.load(f)[f"{city.lower()}_bookings"]
    
    filtered = [d for d in bookings if condition(d)]
    with open(f"{city.lower()}_smaller_than_{range}.json","w+") as f:
        json.dump({f"{city.lower()}_bookings":filtered},f)
    print(f"less than {range} stored")
    
def store_whole_booking(city,num_of_pages):
    overall_booking_info = []
    print(f"Extracting flight data for {city}...")
    for i in tqdm(range(1,num_of_pages+1)):
        params = {
        "city":city,
        "checkin_date":"2024-8-15",
        "checkout_date":"2024-8-22",
        "purpose":"work",
        "num_of_adults":10,
        "num_of_rooms":5,
        "num_of_children":0,
        "page_num":i
        }
        url = CaesarHotelBooking.create_url(**params)
        bookinginfo = CaesarHotelBooking.caesar_get_hotel_info(url)
        overall_booking_info.append(bookinginfo)
    full_bookings = list(itertools.chain(*overall_booking_info))
    with open(f"{city.lower()}_bookings.json","w+") as f:
        json.dump({"url":url,f"{city.lower()}_bookings":full_bookings},f)
    print(full_bookings)
    print(len(full_bookings))
def main():
    # TODO Check out Expedia...
    try:
        city = sys.argv[1]
        max_amount = float(sys.argv[2]) # 3000
    except IndexError as iex:
        print("python caesarhotelbooking.py <city_to_book>")
    num_of_pages = 10
    store_whole_booking(city,num_of_pages)

    store_lower_than_3000(city,max_amount)

if __name__ == "__main__":
    main()
