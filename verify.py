import pandas as pd
import numpy as np

sub_df = pd.read_csv("cn_sub.csv", names=["Courier_id", "Addr", "Arrival_time", "Departure", "Amount", "Order_id"])

SPEED = 15*1000.0/60
site_df = pd.read_csv("1.csv")
spot_df = pd.read_csv("2.csv")
shop_df = pd.read_csv("3.csv")
ds_order_df = pd.read_csv("4.csv")
o2o_order_df = pd.read_csv("5.csv")
courier_df = pd.read_csv("6.csv")
node_lng_dict = {}
node_lat_dict = {}
for i, e in site_df.iterrows():
    node_lng_dict[e.Site_id] = e.Lng
    node_lat_dict[e.Site_id] = e.Lat

for i, e in spot_df.iterrows():
    node_lng_dict[e.Spot_id] = e.Lng
    node_lat_dict[e.Spot_id] = e.Lat

for i, e in shop_df.iterrows():
    node_lng_dict[e.Shop_id] = e.Lng
    node_lat_dict[e.Shop_id] = e.Lat

def time2min(time):
    ts = pd.to_datetime(time, format="%H:%M")
    return ts.hour*60+ts.minute-480

def cal_distance(node1, node2):
    global node_lng_dict, node_lat_dict
    lng1 = node_lng_dict[node1]
    lat1 = node_lat_dict[node1]
    lng2 = node_lng_dict[node2]
    lat2 = node_lat_dict[node2]
    R = 6378137.0
    d_lat = (lat1-lat2)/2.0
    d_lng = (lng1-lng2)/2.0
    S = 2*R*np.arcsin(np.sqrt(np.power(np.sin(np.pi/180*d_lat),2)+np.cos(np.pi/180*lat1)*np.cos(np.pi/180*lat2)*np.power(np.sin(np.pi/180*d_lng),2)))
    return S

def cal_cost(node1, node2):
    global SPEED
    return np.round(cal_distance(node1, node2)/SPEED)

def cal_proctime(x):
    return np.round(3*np.sqrt(x)+5)

arranges = []
for i in range(1, 1001):
    arrange = sub_df[sub_df.Courier_id==("D%04d"%i)]
    if len(arrange)==0:
        continue
    arranges.append(arrange)

def verify2(arrange):
    departure = arrange.iloc[0].Departure
    for i in range(1, len(arrange)):
        arrival_time = arrange.iloc[i].Arrival_time
        if arrival_time < departure:
            return False
        departure = arrange.iloc[i].Departure
    return True

def verify3(arrange):
    for i in range(0, len(arrange)):
        arrival_time = arrange.iloc[i].Arrival_time
        departure = arrange.iloc[i].Departure
        if departure < arrival_time:
            return False
    return True

def verify9(arrange, ds_order_df, o2o_order_df):
    # use the example to verify cal functions
    #mix_path = ["A083","A083","A083","A083","A083","B5800","B7555","B7182","B8307","B8461","A083","A083","A083","B6528","S245","B3266","B3266","B2337","A083","A083","A083","A083","S294","B1940","B6104","B8926","B9072","B6103"]
    #orders = ["F6344","F6360","F6358","F6353","F6354","F6344","F6354","F6353","F6358","F6360","F6349","F6325","F6314","F6349","E0895","E0895","F6325","F6314","F6366","F6345","F6346","F6308","E1088","F6308","F6346","E1088","F6366","F6345"]   
    mix_path = arrange.Addr.tolist()
    orders = arrange.Order_id.tolist()
    mix_arrange_df = pd.DataFrame({ "Addr": mix_path, "Order_id": orders})
    mix_arrange_df["Courier_id"] = arrange.iloc[0].Courier_id
    mix_arrange_df["Arrival_time"] = arrange.iloc[0].Arrival_time
    mix_arrange_df["Departure"] = arrange.iloc[0].Departure
    mix_arrange_df["Amount"] = 0
    pre_e = mix_arrange_df.iloc[0]
    pre_addr = pre_e.Addr
    pre_order = pre_e.Order_id
    pre_departure = arrange.iloc[0].Departure
    if 'F' in pre_order:
        amount = ds_order_df[ds_order_df["Order_id"]==pre_order].Num.values[0]
    elif 'E' in pre_order:
        amount = o2o_order_df[o2o_order_df["Order_id"]==pre_order].Num.values[0]
    new_mix_arrange_df = pd.DataFrame({"Courier_id": [arrange.iloc[0].Courier_id], "Addr": [pre_addr], "Arrival_time": [arrange.iloc[0].Arrival_time], "Departure": [arrange.iloc[0].Departure], "Amount": [amount],  "Order_id": [pre_order]})
    for i in range(1, len(mix_arrange_df)):
        cur_e = mix_arrange_df.iloc[i]
        cur_addr = cur_e.Addr
        cur_order = cur_e.Order_id
        if 'A' in cur_addr:
            arrival_time = pre_departure + cal_cost(pre_addr, cur_addr)
            amount = ds_order_df[ds_order_df["Order_id"]==cur_order].Num.values[0]
            departure = arrival_time
        elif 'B' in cur_addr and 'F' in cur_order:
            arrival_time = pre_departure + cal_cost(pre_addr, cur_addr)
            amount = -ds_order_df[ds_order_df["Order_id"]==cur_order].Num.values[0]
            departure = arrival_time + cal_proctime(abs(amount))
        elif 'B' in cur_addr and 'E' in cur_order:
            arrival_time = pre_departure + cal_cost(pre_addr, cur_addr)
            amount = -o2o_order_df[o2o_order_df["Order_id"]==cur_order].Num.values[0]
            departure = arrival_time + cal_proctime(abs(amount))
        elif 'S' in cur_addr:
            arrival_time = pre_departure + cal_cost(pre_addr, cur_addr)
            amount = o2o_order_df[o2o_order_df["Order_id"]==cur_order].Num.values[0]
            departure = max(time2min(o2o_order_df[o2o_order_df["Order_id"]==cur_order].Pickup_time.values[0]), arrival_time)
        new_mix_arrange_df = new_mix_arrange_df.append(pd.DataFrame({"Courier_id": [arrange.iloc[0].Courier_id], "Addr": [cur_addr], "Arrival_time": [arrival_time], "Departure": [departure], "Amount": [amount],  "Order_id": [cur_order]}))
        cmp_e = arrange.iloc[i]
        if cur_addr != cmp_e.Addr or amount != cmp_e.Amount or arrival_time != cmp_e.Arrival_time or departure != cmp_e.Departure:
            print "arrange %d" % i
            return False
        pre_addr = cur_addr
        pre_departure = departure
    return True


def  verify_v5(sub_df, o2o_order_df, ds_order_df):
    sub_df_sort = sub_df.sort_values(["Order_id", "Departure"], ascending=[1, 1])
    for i in range(0, len(o2o_order_df)*2, 2):
        shop_id = sub_df_sort.iloc[i].Addr
        shop_amount = sub_df_sort.iloc[i].Amount
        spot_id = sub_df_sort.iloc[i+1].Addr
        spot_amount = sub_df_sort.iloc[i+1].Amount
        if shop_id != o2o_order_df.iloc[i/2].Shop_id:
            print "o2o shop_id %d" % i
            return False
        if spot_id != o2o_order_df.iloc[i/2].Spot_id:
            print "o2o spot_id %d" % i
            return False
        if shop_amount != o2o_order_df.iloc[i/2].Num:
            print "o2o shop_amount %d" % i
            return False
        if spot_amount != -o2o_order_df.iloc[i/2].Num:
            print "o2o spot_amount %d" % i
            return False
    for i in range(len(o2o_order_df)*2, len(o2o_order_df)*2+len(ds_order_df)*2, 2):
        site_id = sub_df_sort.iloc[i].Addr
        site_amount = sub_df_sort.iloc[i].Amount
        spot_id = sub_df_sort.iloc[i+1].Addr
        spot_amount = sub_df_sort.iloc[i+1].Amount
        if site_id != ds_order_df.iloc[i/2-len(o2o_order_df)].Site_id:
            print "ds site_id %d" % i
            return False
        if spot_id != ds_order_df.iloc[i/2-len(o2o_order_df)].Spot_id:
            print "ds spot_id %d" % i
            return False
        if site_amount != ds_order_df.iloc[i/2-len(o2o_order_df)].Num:
            print "ds site_amount %d" % i
            return False
        if spot_amount != -ds_order_df.iloc[i/2-len(o2o_order_df)].Num:
            print "ds spot_amount %d" % i
            return False
    return True

def  verify_v6(sub_df, o2o_order_df):
    sub_df_sort = sub_df.sort_values(["Order_id", "Departure"], ascending=[1, 1])
    for i in range(0, len(o2o_order_df)*2, 2):
        shop_departure = sub_df_sort.iloc[i].Departure
        if shop_departure < time2min(o2o_order_df.iloc[i/2].Pickup_time):
            print "shop_departure %d" % i
            return False
    return True

def  verify_v7(sub_df, o2o_order_df, ds_order_df):
    sub_df_sort = sub_df.sort_values(["Order_id", "Departure"], ascending=[1, 1])
    for i in range(0, len(o2o_order_df)*2, 2):
        shop_num = sub_df_sort.iloc[i].Amount
        spot_num = sub_df_sort.iloc[i+1].Amount
        if shop_num + spot_num != 0:
            print "shop_num %d" % i
            return False
    for i in range(len(o2o_order_df)*2, len(o2o_order_df)*2+len(ds_order_df)*2, 2):
        site_num = sub_df_sort.iloc[i].Amount
        spot_num = sub_df_sort.iloc[i+1].Amount
        if site_num + spot_num != 0:
            print "site_num %d" % i
            return False
    return True


def verify_v8(sub_df, o2o_order_df, ds_order_df):
    sub_orders = sub_df.Order_id.drop_duplicates().sort_values().tolist()
    raw_orders = o2o_order_df.Order_id.tolist() + ds_order_df.Order_id.tolist()
    return sub_orders == raw_orders

def verify_v10(sub_df):
    sub_amounts = sub_df.Amount.tolist()
    sub_total_amounts = pd.Series(np.cumsum(sub_amounts))
    return len(sub_total_amounts[sub_total_amounts>140]) == 0

def  verify_v11(sub_df):
    sub_df_sort = sub_df.sort_values(["Order_id", "Departure"], ascending=[1, 1])
    for i in range(0, len(sub_df_sort), 2):
        pick_addr = sub_df_sort.iloc[i].Addr
        send_addr = sub_df_sort.iloc[i+1].Addr
        if ('S' not in pick_addr) and ('A' not in pick_addr):
            return False
        if ('B' not in send_addr):
            return False
    return True

v2 = np.array(map(lambda arrange: verify2(arrange), arranges))
if len(v2[v2==False])==0:
    print "pass v2"
else:
    print "V2 FAILED"

v3 = np.array(map(lambda arrange: verify3(arrange), arranges))
if len(v3[v3==False])==0:
    print "pass v3"
else:
    print "V3 FAILED"

if len(sub_df.Order_id) == 2*(len(ds_order_df)+len(o2o_order_df)) and len(sub_df.Order_id.drop_duplicates()) == len(ds_order_df)+len(o2o_order_df):
    print "pass v4"
else:
    print "V4 FAILED"

if verify_v5(sub_df, o2o_order_df, ds_order_df) == True:
    print "pass v5"
else:
    print "V5 FAILED"

if verify_v6(sub_df, o2o_order_df) == True:
    print "pass v6"
else:
    print "V6 FAILED"

if verify_v7(sub_df, o2o_order_df, ds_order_df) == True:
    print "pass v7"
else:
    print "V7 FAILED"

if verify_v8(sub_df, o2o_order_df, ds_order_df) == True:
    print "pass v8"
else:
    print "V8 FAILED"

v9 = np.array(map(lambda arrange: verify9(arrange, ds_order_df, o2o_order_df), arranges))
if len(v9[v9==False])==0:
    print "pass v9"
else:
    print "V9 FAILED"

if verify_v10(sub_df) == True:
    print "pass v10"
else:
    print "V10 FAILED"

if verify_v11(sub_df) == True:
    print "pass v11"
else:
    print "V11 FAILED"
    
# total costs
sum(map(lambda arrange: arrange.iloc[-1].Departure, arranges))

