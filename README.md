# DonkeyCar + kohandatud juhtimissüsteem (Teleop)

Selles juhendis seadistame DonkeyCari kaugjuhtimise lahenduse, mis koosneb:

* WebSocket-põhisest juhtimisliidesest
* HTTP API-st (sh /autonomy, /recording, /ping)
* Videopildi reaalajas saatmisest brauserisse
* CORS-tuge ja Flask-serverit kasutavast haldusliidesest

---

## Eeltingimused

Seda setup’i on testitud ja kinnitatud järgmistel tingimustel:
* Raspberry Pi 4 Model B Rev 1.5
* Raspberry Pi OS (Debian 11 "Bullseye")
* Python 3.9.2
* DonkeyCar v5.0.0

---

## 1. Klooni projekt

Esmalt klooni projekt:

```bash
git clone https://github.com/MarkkusKoddala/donkey-teleop-controller.git
```
---

## 2. Loo sõiduki projekt

Loo sõiduki projekt samasse kausta:

```bash
donkeycar createcar --path ./donkey-teleop-controller/
cd donkey-teleop-controller
```
---

## 3. paigalda vajalikud sõltuvused

```bash
pip install -r requirements.txt
```
---

## 3. Asenda `myconfig.py` fail


```python
cp my_preconfig.py myconfig.py
```

---

## 4. muuda `manage.py` faili

Ava `manage.py` ja leia funktsioon `add_user_controller(...)`. Lisa funktsiooni algusesse:

```python
if cfg.USE_CUSTOM_CONTROLLER:
    from core.teleop_control_part import TeleopControlPart

    controller = TeleopControlPart(cfg)

    V.add(
        controller,
        inputs=['cam/image_array'],
        outputs=['user/angle', 'user/throttle', 'user/mode', 'recording', 'cam/image_array'],
        threaded=True
    )

    print("Kasutusel on kohandatud juhtimissüsteem.")
    return controller
```

Tuleb arvestada, et mõnel DonkeyCari versioonil on liidese lisamine natukene teistmoodi.
---

## 5. käivita auto

```bash
python manage.py drive
```
---

## 6. (valikuline) kasuta kaasasolevat mudelit
Kaustas resources on kaasas eelnevalt treenitud mudel, nt delta_model.h5. Saad seda kasutada testimiseks järgmise käsuga:
```bash
python manage.py drive --model=resources/delta_model.h5
```

