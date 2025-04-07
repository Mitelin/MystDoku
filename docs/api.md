# 📘 MystDoku API – Scoreboard

Tato dokumentace popisuje REST API endpointy pro získání dat o skóre hráčů ve hře MystDoku.

---

## 🔗 Base URL
```
/score/api/scoreboard/
```

---

## 📥 Request

### Metoda: `GET`

### Parametry:
- **Žádné** – API vrací všechna skóre.

---

## 📤 Response

```json
[
  {
    "username": "Mitelin",
    "total_completed_games": 3,
    "completed_easy": 3,
    "completed_medium": 0,
    "completed_hard": 0,
    "best_time_easy": 4.1,
    "best_time_medium": null,
    "best_time_hard": null,
    "unlocked_memories": 6
  },
  ...
]
```

---

## 🧠 Popis polí:

| Pole                   | Význam                                      |
|------------------------|---------------------------------------------|
| `username`             | Přihlašovací jméno hráče                    |
| `total_completed_games` | Celkový počet dokončených her              |
| `completed_easy`       | Dokončené hry na obtížnost "easy"          |
| `completed_medium`     | Dokončené hry na obtížnost "medium"        |
| `completed_hard`       | Dokončené hry na obtížnost "hard"          |
| `best_time_easy`       | Nejrychlejší čas na easy (v sekundách)     |
| `best_time_medium`     | Nejrychlejší čas na medium (v sekundách)   |
| `best_time_hard`       | Nejrychlejší čas na hard (v sekundách)     |
| `unlocked_memories`    | Počet odemčených vzpomínek hráče (max 60)  |

---

## 🔒 Autentizace

Není vyžadována – přístupné všem.

---

## 📝 Poznámky
- Výstup je **neseřazený**.
- Žádné stránkování – API vrací všechna dostupná data.
- Jedná se o **čisté JSON API** bez formátování nebo HTML.