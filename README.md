# Open Prices backend

A Python Django REST API designed to interact with the Open Food Facts _Open Prices_ database.

## Project documentation

### Links

- Open Prices Frontend app: https://prices.openfoodfacts.org
- Open Prices Frontend repository: https://github.com/openfoodfacts/open-prices-frontend
- Open Prices API: https://prices.openfoodfacts.org/api/docs
- Documentation: https://openfoodfacts.github.io/open-prices
- Wiki: https://wiki.openfoodfacts.org/Project:Open-Prices

### Looking for the Open Prices API?

- Open Prices API Documentation: https://prices.openfoodfacts.org/api/docs
- Make sure you comply with the OdBL licence, mentioning the source of your data, and ensuring to avoid combining non free data you can't release legally as open data. Another requirement is contributing back any product you add using this SDK.
- Please get in touch at reuse@openfoodfacts.org
- We are very interested in learning what the Open Prices data is used for. It is not mandatory, but we would very much appreciate it if you tell us about your re-uses (https://forms.gle/hwaeqBfs8ywwhbTg8) so that we can share them with the Open Food Facts community. And we would be happy to feature it here: https://prices.openfoodfacts.org/community

### 🎨 Design & User interface

- The Open Prices server is exposed through the Mobile App and the Open Prices frontend (and probably elsewhere in the future, thanks to web components)
- We strive to thoughtfully design every feature before we move on to implementation, so that we respect Open Food Facts' graphic charter and nascent design system, while having efficient user flows.
- [![Figma](https://img.shields.io/badge/figma-%23F24E1E.svg?logo=figma&logoColor=white) Mockups for Open Prices](https://www.figma.com/design/cIB7CInl2BfueMzWnz09t6/Open-Prices?node-id=0-1&p=f&t=LC7UvPjngw57NGSs-0)
- [![Figma](https://img.shields.io/badge/figma-%23F24E1E.svg?logo=figma&logoColor=white) Mobile Mockups for Open Prices](https://www.figma.com/design/nFMjewFAOa8c4ahtob7CAB/Mobile-App-Design--Quentin-?node-id=5816-22697&p=f&t=AkgTM9QzMK7tQeGC-0)
- [![Figma](https://img.shields.io/badge/figma-%23F24E1E.svg?logo=figma&logoColor=white) Benchmark of the defunct Prixing app](https://www.figma.com/design/XQYkLGKlcotBPpwKMhDe1z/Prixing---Benchmark?m=auto&t=AkgTM9QzMK7tQeGC-6)
- Are you a designer ? [Join the design team](https://github.com/openfoodfacts/openfoodfacts-design)

## Dependencies

* Python 3.11
* [Django](https://www.djangoproject.com/) framework
* PostgreSQL database

## How to install on your local machine and help develop Open Prices

Follow the steps in [INSTALL.md](https://github.com/openfoodfacts/open-prices/blob/main/INSTALL.md), [local-development.md](https://github.com/openfoodfacts/open-prices/blob/main/docs/local-development.md) and [maintenance.md](https://github.com/openfoodfacts/open-prices/blob/main/docs/maintenance.md)

## Contribute

See [CONTRIBUTING.md](https://github.com/openfoodfacts/open-prices/blob/main/CONTRIBUTING.md)

<details>
<summary><h2>Weekly meetings</h2></summary>
* We e-meet Thrusdays at 14:00 Paris Time
* ![Google Meet](https://img.shields.io/badge/Google%20Meet-00897B?logo=google-meet&logoColor=white) Video call link: https://meet.google.com/oin-hiqp-tmd
* Join by phone: https://tel.meet/oin-hiqp-tmd?pin=5784334159966
* Add the Event to your Calendar by [adding the Open Food Facts community calendar to your calendar](https://wiki.openfoodfacts.org/Events)
* [Weekly Agenda](https://docs.google.com/document/u/0/d/1-OfMAi-cB7mi9_q172EbBCWHkfKDM0zVg4wzULW3pFY/edit): please add the Agenda items as early as you can.
* Make sure to check the Agenda items in advance of the meeting, so that we have the most informed discussions possible.
* The meeting will handle Agenda items first, and if time permits, collaborative bug triage.
* We strive to timebox the core of the meeting (decision making) to 30 minutes, with an optional free discussion/live debugging afterwards.
* We take comprehensive notes in the Weekly Agenda of agenda item discussions and of decisions taken.
</details>
