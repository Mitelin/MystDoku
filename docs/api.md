# 📘 MystDoku API – Scoreboard

This documentation describes the REST API endpoint for retrieving player score data in the game **MystDoku**.

---

## 🔗 Base URL
```
/score/api/scoreboard/
```

---

## 📥 Request

### Method: `GET`

### Parameters:
- **None** – the API returns all scores.

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

## 🧠 Field Descriptions:

| Field                  | Description                                   |
|------------------------|-----------------------------------------------|
| `username`             | Player's login name                           |
| `total_completed_games`| Total number of completed games               |
| `completed_easy`       | Games completed on "easy" difficulty          |
| `completed_medium`     | Games completed on "medium" difficulty        |
| `completed_hard`       | Games completed on "hard" difficulty          |
| `best_time_easy`       | Fastest time on easy (in seconds)             |
| `best_time_medium`     | Fastest time on medium (in seconds)           |
| `best_time_hard`       | Fastest time on hard (in seconds)             |
| `unlocked_memories`    | Number of unlocked memories (max 60)          |

---

## 🔒 Authentication

Not required – publicly accessible.

---

## 📝 Notes
- The output is **unsorted**.
- No pagination – the API returns all available data at once.
- This is a **pure JSON API** with no formatting or HTML.
