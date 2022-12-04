# %%
import pandas as pd
from tqdm import tqdm
import datetime
from collections import defaultdict
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
raw_chatted_event_df

# %%
main_df = label_df

# %%
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

    for item_id in [228242, 224690, 220210, 224689, 220179, 225309, 223762, 227243, 220045, 224167, 223761, 220050]:
        s_time = start_time
        e_time = start_time + datetime.timedelta(days=1)

        event_result = raw_chatted_event_df[(raw_chatted_event_df["subject_id"] == subject_id) & (raw_chatted_event_df["hadm_id"] == hadm_id) & (raw_chatted_event_df["itemid"] == item_id)]
        event_list = list()
        for index, event_row in event_result.iterrows():
            event_list += [{
                "charttime": datetime.datetime.strptime(event_row["charttime"], "%Y-%m-%d %H:%M:%S"),
                "value": event_row["value"]
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

            feature[time_point][item_id]  = {
                "label": item_id,
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
            "HR_max": feature[timepoint][220045]["max"],
            "HR_min": feature[timepoint][220045]["min"],
            "PtS_max": feature[timepoint][228242]["max"],
            "PtS_min": feature[timepoint][228242]["min"],
            "Respiratory Rate (Total)_max": feature[timepoint][224690]["max"],
            "Respiratory Rate (Total)_min": feature[timepoint][224690]["min"],
            "Respiratory Rate_max": feature[timepoint][220210]["max"],
            "Respiratory Rate_min": feature[timepoint][220210]["min"],
            "Respiratory Rate (spontaneous)_max": feature[timepoint][224689]["max"],
            "Respiratory Rate (spontaneous)_min": feature[timepoint][224689]["min"],
            "NBPs_max": feature[timepoint][220179]["max"],
            "NBPs_min": feature[timepoint][220179]["min"],
            "ART BP Systolic_max": feature[timepoint][225309]["max"],
            "ART BP Systolic_min": feature[timepoint][225309]["min"],
            "Temperature C_max": feature[timepoint][223762]["max"],
            "Temperature C_min": feature[timepoint][223762]["min"],
            "Manual BPs R_max": feature[timepoint][227243]["max"],
            "Manual BPs R_min": feature[timepoint][227243]["min"],
            "Manual BPs L_max": feature[timepoint][224167]["max"],
            "Manual BPs L_min": feature[timepoint][224167]["min"],
            "Temperature F_max": feature[timepoint][223761]["max"],
            "Temperature F_min": feature[timepoint][223761]["min"],
            "ABPs_max": feature[timepoint][220050]["max"],
            "ABPs_min": feature[timepoint][220050]["min"],
        }]
df = pd.DataFrame(rows)

df.to_csv(f"../data/result_{sp}_{ep}.csv")

# %%



