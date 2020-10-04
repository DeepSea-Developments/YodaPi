# YodaPi
<img src='https://images-na.ssl-images-amazon.com/images/I/516oRhx3HoL._AC_SL1153_.jpg' width="35%" >

YodaPi (pronounced YODA as in star wars' yoda, and PI as in raspberry pi) is a framework (or base project?) to develop professional applications for raspberry pi without the need to go through all the steps of setting up things step by step.

The name is based on bby yoda (pls disney dont sue me)

## Status
Still baby yoda. Not releases yet. If you have an idea how this project could be an amazing open source project, feel free to fork, or write me @ nick@dsd.dev :)
* created on October 2020. 

## What can you do with this?

The objetive is to deploy very fast projects on raspberry pi that needs databsases (sqlite), connected to the cloud, that might or might not need graphical interface (served as webpage using flask), but that will benefit to have one at least for fast configuration on the field. Also takes advantage of the raspberry pi with wifi, so it creates it's own access point to be able to connect and then configure to a local network for having continuous internet conection.

## Bulletpoint features
* Kiosk mode enabled by default (showing webpage through HDMI).
* Preloaded with <a href="http://supervisord.org/">Supervisord</a> so your app runs when the RPI boots.
* Automatically creates hotspot if notin a know wifi network, or automatically connecting to known network. If IP is unknown, you can plug the hdmi interface where the webpage displays it, or connect with an app.
* Based on <a  href="https://www.ros.org/">ROS</a>, in the way that there is a CORE and several microservises(?) that connects using a PUB/SUB architecture (like mqtt). To achieve this <a href="https://zeromq.org/">ZeroMQ</a> is used. 
* Lightweight database is used. *SQLite* managed with python <a href="https://www.sqlalchemy.org/">sqlalchemy</a>
* Python's <a href="https://flask.palletsprojects.com/en/1.1.x/">Flask</a> is used to serve a webpage. Using <a href="https://jinja.palletsprojects.com/en/2.11.x/">Jinja</a> templates to make everything more organized.
* Using <a href="https://getbootstrap.com/docs/4.3/getting-started/introduction/">Bootstrap</a> for making fast webpages. (even though not sure if its the best option for embedded systems)

* [near future] Flutter app that connects via bluetooth with the raspberry pi to set wifi network or to send more information/data.

## Examples of projects done with YodaPi
### TermoDeep
A thermal camera solution -> www.termodeep.com

<img src="https://i.ytimg.com/vi/NKib-1CkmDg/hqdefault.jpg">

### Door access controller (in progress)
