require 'rubygems'
require 'json'
require 'pp'

json = File.read('../../data/noaa_station_list.json')
stations = JSON.parse(json)

pp stations
