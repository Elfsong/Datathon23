# %%
import pandas as pd
from tqdm import tqdm
import datetime
from collections import defaultdict
from sql import SqlMiddleware
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--sp",
    default=0,
    type=int,
)
parser.add_argument(
    "--ep",
    default=-1,
    type=int,
)
args = parser.parse_args()

sp = args.sp
ep = args.ep

# %%
label_df = pd.read_csv('../data/label.csv')
raw_labevents_df = pd.read_csv('../data/raw_labevents.csv')
raw_patientsinfo_df = pd.read_csv('../data/raw_patientsinfo.csv')
raw_procedureevents_df = pd.read_csv('../data/raw_procedureevents.csv')
raw_chatted_event_df = pd.read_csv('../data/raw_chart_event.csv')

# %%
main_df = label_df

# %%
# Age Gender
main_df = main_df.merge(raw_patientsinfo_df, on='subject_id', how='left')

# %%
rows = list()

for index, row in tqdm(list(main_df.iterrows())[sp:ep]):
    subject_id = row['subject_id']
    hadm_id = row['hadm_id']
    clabsi_label = row['clabsi']
    gender = row["gender"]
    age = row["age"]
    
    Invasive_table = raw_procedureevents_df[(raw_procedureevents_df["subject_id"] == subject_id) & (raw_procedureevents_df["hadm_id"] == hadm_id)]
    starttimes = [datetime.datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S") for t_str in Invasive_table["starttime"]]
    endtimes = [datetime.datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S") for t_str in Invasive_table["endtime"]]

    # Start time and End time
    start_time = sorted(starttimes)[0]
    end_time = sorted(endtimes)[-1] + datetime.timedelta(days=2)

    feature = dict()

    for label in ["Temperature", "Glucose", "Sodium", "Intubated", "Lactate", "White Blood Cells", "Platelet Count"]:
        s_time = start_time
        e_time = start_time + datetime.timedelta(days=1)

        event_result = raw_labevents_df[(raw_labevents_df["subject_id"] == subject_id) & (raw_labevents_df["hadm_id"] == hadm_id) & (raw_labevents_df["label"] == label)]
        event_list = list()
        for index, event_row in event_result.iterrows():
            event_list += [{
                "charttime": datetime.datetime.strptime(event_row["charttime"], "%Y-%m-%d %H:%M:%S"),
                "value": event_row["valuenum"]
            }]

        time_point = 0
        while e_time <= end_time:
            if time_point not in feature:
                feature[time_point] = dict()

            s_time += datetime.timedelta(days=1)
            e_time += datetime.timedelta(days=1)

            temp_list = list()
            for event in event_list:
                if event["charttime"] >= s_time and event["charttime"] < e_time:
                    temp_list += [float(event["value"])]

            feature[time_point][label]  = {
                "label": label,
                "time_point": time_point,
                "max": max(temp_list) if temp_list else None,
                "min": min(temp_list) if temp_list else None, 
                "average": (sum(temp_list) / len(temp_list)) if temp_list else None, 
            }
            time_point += 1    
    
    for timepoint in feature:
        rows += [{
            "subject_id": subject_id,
            "hadm_id": hadm_id,
            "timepoint": timepoint,
            "clabsi": clabsi_label,
            "gender": gender,
            "age": age,
            "Temperature_max": feature[timepoint]["Temperature"]["max"],
            "Temperature_min": feature[timepoint]["Temperature"]["min"],
            "WBC_max": feature[timepoint]["White Blood Cells"]["max"],
            "WBC_min": feature[timepoint]["White Blood Cells"]["min"],
            "Glucose_max": feature[timepoint]["Glucose"]["max"],
            "Glucose_min": feature[timepoint]["Glucose"]["min"],
            "Sodium_max": feature[timepoint]["Sodium"]["max"],
            "Sodium_min": feature[timepoint]["Sodium"]["min"],
            "Intubated_max": feature[timepoint]["Intubated"]["max"],
            "Intubated_min": feature[timepoint]["Intubated"]["min"],
            "Lactate_max": feature[timepoint]["Lactate"]["max"],
            "Lactate_min": feature[timepoint]["Lactate"]["min"],
            "PLE_max": feature[timepoint]["Platelet Count"]["max"],
            "PLE_min": feature[timepoint]["Platelet Count"]["min"],
        }]
df = pd.DataFrame(rows)

df.to_csv(f"../data/result_{sp}_{ep}.csv")



