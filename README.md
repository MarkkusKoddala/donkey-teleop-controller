# DonkeyCar + kohandatud juhtimissüsteem (Teleop)

Selles juhendis seadistame DonkeyCari koos kaugjuhtimise lahendusega, mis kasutab WebSocketi, HTTP API-t ja videopilti.

---

## Eeltingimused

* DonkeyCar on juba eelnevalt paigaldatud
* DonkeyCar installitud (testitud versiooniga 4.3.22)
* Raspberry Pi 4 platvorm
* Soovituslikult töötad virtuaalkeskkonnas (venv)

---

## 1. Klooni projekt

Esmalt klooni oma kohandatud DonkeyCar projekt:

```bash
git clone https://github.com/MarkkusKoddala/donkey-teleop-controller.git
cd donkey-teleop-controller
```

(Vaheta link oma GitHub repo vastu.)

---

## 2. aktiveeri virtuaalkeskkond

Aktiveeri olemasolev keskkond, mille lõid donkeycari installides ja projekti luues:
```bash
source env/bin/activate
```

---

## 3. paigalda vajalikud sõltuvused

```bash
pip install -r requirements.txt
```

Kui kasutad TensorFlow’i ARM versiooni (nt Raspberry Pi puhul), paigalda see käsitsi:

```bash
pip install opencv-contrib-python-headless==4.5.1.48 --extra-index-url https://www.piwheels.org/simple
```

---

## 4. lisa `myconfig.py` faili järgmine rida

Ava `myconfig.py` ja lisa (või muuda) järgmine seadistus:

```python
USE_CUSTOM_CONTROLLER = True
```

---

## 6. muuda `manage.py` faili

Ava `manage.py` ja leia funktsioon `add_user_controller(...)`. Lisa funktsiooni algusesse:

```python
if cfg.USE_CUSTOM_CONTROLLER:
    from controller.teleop_control_part import TeleopControlPart

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

---

## 7. käivita auto

```bash
python manage.py drive
```
---

## 8. (valikuline) kasuta kaasasolevat mudelit
Kaustas resources on kaasas eelnevalt treenitud mudel, nt delta_model.h5. Saad seda kasutada testimiseks järgmise käsuga:
```bash
python manage.py drive --model=resources/delta_model.h5
```

