#!/usr/bin/env python3
"""
LogListener 可观测仪表盘生成器
场景化设计：总览 → 吞吐延迟 → 队列积压 → 数据质量 → 发送链路 → 异常事件 → 资源水位
"""
import json, uuid, subprocess, sys

TID = "cls-service-metric-internal-12-1254077820"
RID = 12
IP = "${IP}"

def uid():
    return f"chart-{uuid.uuid4()}"

def tgt(q, ref="A"):
    return {"refId":ref,"regionId":RID,"TopicId":TID,"Query":q,"SyntaxRule":1,
            "datasourceType":"metric","datasource":None,"step":None,"stepUnit":"s",
            "metricQueryType":"range","SamplingRate":1}

def row_panel(title, y, collapsed=False):
    return {"id":uid(),"title":title,"independentTime":None,"timezone":None,"description":None,
            "gridPos":{"x":0,"y":y,"w":24,"h":1},"type":"row",
            "target":{"regionId":None,"TopicId":"","Query":"","SyntaxRule":1,"refId":"A"},
            "targets":[{"refId":"A","regionId":None,"TopicId":"","Query":"","SyntaxRule":1}],
            "options":{},"fieldConfig":{"defaults":{},"overrides":[]},"transformations":[],
            "collapsed":collapsed,"panels":[]}

def stat(title, query, x, y, w=4, h=6, unit="", dec=2, thresholds=None, desc=None, text_mode="value_and_name_and_sparkline"):
    if not thresholds:
        thresholds = [{"value":None,"color":"rgba(68,191,154,1)"}]
    t = tgt(query)
    return {"id":uid(),"title":title,"independentTime":None,"timezone":None,"description":desc,
            "gridPos":{"x":x,"y":y,"w":w,"h":h},"type":"stat","target":t,"targets":[t],
            "options":{"xAxis":{"fields":{}},"yAxis":{"fields":{}},
                       "textMode":text_mode,"compareType":"Percent","compareDurations":"P1D",
                       "reduceOptions":{"values":False,"limit":1000,"calcs":["lastNotNull"]},
                       "legend":{"displayMode":"table","placement":"bottom","calcs":["mean","max","min","lastNotNull"]},
                       "tooltip":{"mode":"multi","sort":"desc"}},
            "fieldConfig":{"defaults":{"decimals":dec,
                           "thresholds":{"mode":"absolute","steps":thresholds},
                           "color":{"mode":"thresholds"},"unit":unit},"overrides":[]},
            "transformations":[]}

def ts(title, queries, x, y, w=12, h=8, unit="", dec=2, desc=None, stack="none", fill=25,
       thresholds=None, th_style="off"):
    if not thresholds:
        thresholds = [{"value":None,"color":"rgba(68,191,154,1)"}]
    if isinstance(queries, str):
        queries = [queries]
    targets = [tgt(q, chr(65+i)) for i,q in enumerate(queries)]
    return {"id":uid(),"title":title,"independentTime":None,"timezone":None,"description":desc,
            "gridPos":{"x":x,"y":y,"w":w,"h":h},"type":"timeseries","target":targets[0],"targets":targets,
            "options":{"xAxis":{"fields":{}},"yAxis":{"fields":{}},"zAxis":{"fields":{}},
                       "legend":{"displayMode":"table","placement":"bottom","calcs":["mean","max","min","lastNotNull"]},
                       "tooltip":{"mode":"multi","sort":"desc"},"compareType":"None","compareDurations":"P1D"},
            "fieldConfig":{"defaults":{"custom":{"drawStyle":"line","lineInterpolation":"smooth",
                           "lineWidth":2,"gradientMode":"auto","fillOpacity":fill,
                           "showPoints":"auto","pointSize":6,"nullPointMode":"connected",
                           "stacking":{"mode":stack},"axisPlacement":"auto",
                           "axisSoftMin":None,"axisSoftMax":None,
                           "scaleDistribution":{"type":"linear"},
                           "hideFrom":{"viz":False,"tooltip":False,"legend":False},
                           "showSeriesLineCount":100,"thresholdsStyle":{"mode":th_style}},
                           "decimals":dec,"thresholds":{"mode":"absolute","steps":thresholds},
                           "color":{"mode":"palette-classic"},"unit":unit,"links":[]},"overrides":[]},
            "transformations":[]}

def gauge(title, query, x, y, w=4, h=6, unit="%", dec=1, thresholds=None):
    if not thresholds:
        thresholds = [{"value":None,"color":"rgba(68,191,154,1)"},{"value":50,"color":"rgba(255,193,7,1)"},{"value":80,"color":"rgba(245,54,54,1)"}]
    t = tgt(query)
    return {"id":uid(),"title":title,"independentTime":None,"timezone":None,"description":None,
            "gridPos":{"x":x,"y":y,"w":w,"h":h},"type":"gauge","target":t,"targets":[t],
            "options":{"reduceOptions":{"values":False,"limit":1000,"calcs":["lastNotNull"]},
                       "showThresholdLabels":False,"showThresholdMarkers":True},
            "fieldConfig":{"defaults":{"decimals":dec,"min":0,"max":100,
                           "thresholds":{"mode":"absolute","steps":thresholds},
                           "color":{"mode":"thresholds"},"unit":unit},"overrides":[]},
            "transformations":[]}

# PromQL helpers
def q(metric, extra=""):
    base = f"{metric}{{IP='{IP}'}}"
    if extra:
        return f"{extra}"
    return base

def rate_q(metric, window="5m"):
    return f"rate({metric}{{IP='{IP}'}}[{window}]) or vector(0)"

def safe_q(metric):
    return f"{metric}{{IP='{IP}'}} or vector(0)"

# ========== BUILD ==========
P = []
y = 0

# ===== Section 0: 采集健康度总览 =====
P.append(row_panel("📊 采集健康度总览", y)); y+=1

# 北极星: 采集延迟
GREEN = "rgba(68,191,154,1)"
YELLOW = "rgba(255,193,7,1)"
ORANGE = "rgba(255,120,10,1)"
RED = "rgba(245,54,54,1)"

P.append(stat("⏱ 采集延迟（预估）",
    f"(file_lag_size{{IP='{IP}'}}) / (rate(input_size{{IP='{IP}'}}[5m]) > 0 or vector(1))",
    0, y, w=8, h=8, unit="s", dec=0,
    thresholds=[{"value":None,"color":GREEN},{"value":30,"color":YELLOW},{"value":300,"color":ORANGE},{"value":1800,"color":RED}],
    desc="采集延迟 = 待采集量 / 采集速率。<30s绿 | 30s~5min黄 | 5~30min橙 | >30min红"))

P.append(stat("📥 采集速率", rate_q("input_size"), 8,y, w=4,h=4, unit="Bps",dec=1))
P.append(stat("📊 待采集积压", safe_q("file_lag_size"), 12,y, w=4,h=4, unit="decbytes",dec=1,
    thresholds=[{"value":None,"color":GREEN},{"value":10485760,"color":YELLOW},{"value":104857600,"color":RED}]))
P.append(stat("🔴 丢弃率",
    f"(rate(dropped_log_count{{IP='{IP}'}}[5m]) or vector(0)) / (rate(processor_success_count{{IP='{IP}'}}[5m]) + rate(dropped_log_count{{IP='{IP}'}}[5m]) + 0.001) * 100",
    16,y, w=4,h=4, unit="%",dec=3,
    thresholds=[{"value":None,"color":GREEN},{"value":0.1,"color":YELLOW},{"value":1,"color":RED}]))
P.append(stat("❌ 发送失败率",
    f"(rate(send_failed_count{{IP='{IP}'}}[5m]) or vector(0)) / (rate(send_success_count{{IP='{IP}'}}[5m]) + rate(send_failed_count{{IP='{IP}'}}[5m]) + 0.001) * 100",
    20,y, w=4,h=4, unit="%",dec=3,
    thresholds=[{"value":None,"color":GREEN},{"value":0.1,"color":YELLOW},{"value":1,"color":RED}]))

# 第二排
P.append(stat("✅ 处理成功率",
    f"rate(processor_success_count{{IP='{IP}'}}[5m]) / (rate(processor_success_count{{IP='{IP}'}}[5m]) + rate(dropped_log_count{{IP='{IP}'}}[5m]) + 0.001) * 100 or vector(100)",
    8,y+4, w=4,h=4, unit="%",dec=2,
    thresholds=[{"value":None,"color":RED},{"value":99,"color":YELLOW},{"value":99.9,"color":GREEN}]))
P.append(stat("📤 发送成功率",
    f"rate(send_success_count{{IP='{IP}'}}[5m]) / (rate(send_success_count{{IP='{IP}'}}[5m]) + rate(send_failed_count{{IP='{IP}'}}[5m]) + 0.001) * 100 or vector(100)",
    12,y+4, w=4,h=4, unit="%",dec=2,
    thresholds=[{"value":None,"color":RED},{"value":99,"color":YELLOW},{"value":99.9,"color":GREEN}]))
P.append(stat("🔍 解析成功率",
    f"rate(parse_success_count{{IP='{IP}'}}[5m]) / (rate(parse_success_count{{IP='{IP}'}}[5m]) + rate(json_parse_failures_count{{IP='{IP}'}}[5m]) + 0.001) * 100 or vector(100)",
    16,y+4, w=4,h=4, unit="%",dec=2,
    thresholds=[{"value":None,"color":RED},{"value":99,"color":YELLOW},{"value":99.9,"color":GREEN}]))
P.append(stat("🔔 告警数", safe_q("loglistener_alarm_alarm_count"),20,y+4, w=4,h=4, unit="",dec=0,
    thresholds=[{"value":None,"color":GREEN},{"value":1,"color":YELLOW},{"value":5,"color":RED}]))
y+=8

# 全链路数据流
P.append(ts("全链路数据流（输入 → 处理 → 发送 | 丢弃）",[
    rate_q("input_size"), rate_q("processor_success_size"),
    rate_q("send_success_size"), rate_q("dropped_log_size")
], 0,y, w=24,h=8, unit="Bps",dec=1,
   desc="蓝=输入 绿=处理成功 深绿=发送成功 红=丢弃。健康时三线重合，红线趋零"))
y+=8

# ===== Section 1: 采集吞吐与延迟 =====
P.append(row_panel("🚀 采集吞吐与延迟", y)); y+=1

P.append(ts("采集延迟趋势（秒）",
    f"(file_lag_size{{IP='{IP}'}}) / (rate(input_size{{IP='{IP}'}}[5m]) > 0 or vector(1))",
    0,y, w=12,h=8, unit="s",dec=0,
    thresholds=[{"value":None,"color":GREEN},{"value":30,"color":YELLOW},{"value":300,"color":RED}],
    th_style="area", desc="采集延迟 = file_lag_size / rate(input_size)"))
P.append(ts("文件待采集量趋势", safe_q("file_lag_size"),
    12,y, w=12,h=8, unit="decbytes",dec=0, desc="文件大小 - 已读偏移量"))
y+=8

P.append(ts("采集速率 (bytes/s)", rate_q("input_size"), 0,y, w=6,h=7, unit="Bps"))
P.append(ts("处理条数 (条/s)", rate_q("process_count"), 6,y, w=6,h=7, unit="cps"))
P.append(ts("发送速率 (bytes/s)", rate_q("send_log_size"), 12,y, w=6,h=7, unit="Bps"))
P.append(ts("平均发送耗时 (ms)",
    f"(rate(send_log_time_sum{{IP='{IP}'}}[5m]) or vector(0)) / (rate(send_log_time_count{{IP='{IP}'}}[5m]) > 0 or vector(1))",
    18,y, w=6,h=7, unit="ms"))
y+=7

# ===== Section 2: 队列与积压 =====
P.append(row_panel("📦 队列与积压监控", y)); y+=1

P.append(stat("事件积压", safe_q("events_lag"), 0,y, w=4,h=6, dec=0,
    thresholds=[{"value":None,"color":GREEN},{"value":1000,"color":YELLOW},{"value":10000,"color":RED}]))
P.append(stat("Pipeline队列(bytes)", safe_q("pipeline_queue_size"), 4,y, w=4,h=6, unit="decbytes",dec=0))
P.append(stat("Pipeline队列长度", safe_q("pipeline_queue_count"), 8,y, w=4,h=6, dec=0))
P.append(stat("发送队列(bytes)", safe_q("send_queue_size"), 12,y, w=4,h=6, unit="decbytes",dec=0))
P.append(stat("发送队列长度", safe_q("send_queue_count"), 16,y, w=4,h=6, dec=0))
P.append(stat("Polling事件队列", safe_q("polling_event_queue_size"), 20,y, w=4,h=6, unit="decbytes",dec=0))
y+=6

P.append(ts("事件生产 vs 消费速率",[rate_q("events_produced_total"), rate_q("events_consumed_total")],
    0,y, w=12,h=7, unit="cps", desc="生产≈消费=健康，差值=积压增速"))
P.append(ts("事件消费失败", [rate_q("events_consumed_failed_total")], 12,y, w=12,h=7, unit="cps"))
y+=7

# ===== Section 3: 数据质量 =====
P.append(row_panel("🔍 数据质量（丢弃 / 过滤 / 解析）", y)); y+=1

P.append(ts("丢弃日志趋势",[rate_q("dropped_log_size"), rate_q("dropped_log_count")],
    0,y, w=8,h=7, unit="Bps"))
P.append(ts("过滤日志趋势",[rate_q("total_filter_size"), rate_q("total_filter_count")],
    8,y, w=8,h=7, unit="Bps"))
P.append(ts("截断日志", [safe_q("truncate_log_size")], 16,y, w=8,h=7, unit="decbytes"))
y+=7

P.append(ts("解析成功 vs 各类失败",[
    rate_q("parse_success_count"), rate_q("json_parse_failures_count"),
    rate_q("delimiter_mismatch_failures_count"), rate_q("regex_match_failures_count"),
    rate_q("multi_parse_failures_count")
], 0,y, w=12,h=7, unit="cps", desc="绿=成功, 其他=各类解析失败"))
P.append(ts("时间格式解析",[rate_q("time_format_success_count"), rate_q("time_format_failures_count")],
    12,y, w=6,h=7, unit="cps"))
P.append(ts("多行解析失败",[rate_q("multi_line_parse_failures_count"), rate_q("multi_line_parse_failures_size")],
    18,y, w=6,h=7, unit="cps"))
y+=7

# ===== Section 4: 发送链路 =====
P.append(row_panel("📡 发送链路健康", y)); y+=1

P.append(ts("发送成功/失败/超时 (条/s)",[
    rate_q("send_success_count"), rate_q("send_failed_count"), rate_q("send_timeout_log_count")
], 0,y, w=12,h=8, unit="cps", desc="绿=成功 红=失败 橙=超时"))
P.append(ts("发送数据量 (bytes/s)",[
    rate_q("send_success_size"), rate_q("send_failed_size"), rate_q("send_timeout_log_size")
], 12,y, w=12,h=8, unit="Bps"))
y+=8

P.append(stat("重发次数", safe_q("total_resend"), 0,y, w=4,h=6, dec=0,
    thresholds=[{"value":None,"color":GREEN},{"value":10,"color":YELLOW},{"value":100,"color":RED}]))
P.append(stat("网络错误", safe_q("send_network_error"), 4,y, w=4,h=6, dec=0,
    thresholds=[{"value":None,"color":GREEN},{"value":1,"color":YELLOW},{"value":10,"color":RED}]))
P.append(stat("请求错误", safe_q("request_error"), 8,y, w=4,h=6, dec=0,
    thresholds=[{"value":None,"color":GREEN},{"value":1,"color":YELLOW}]))
P.append(stat("配置参数错误", safe_q("params_invalid_error"), 12,y, w=4,h=6, dec=0,
    thresholds=[{"value":None,"color":GREEN},{"value":1,"color":RED}]))
P.append(ts("重发趋势",[rate_q("total_resend")], 16,y, w=8,h=6, unit="cps"))
y+=6

# ===== Section 5: 异常事件 =====
P.append(row_panel("⚠️ 异常事件监控", y)); y+=1

P.append(stat("文件读取错误", safe_q("file_read_error"), 0,y, w=3,h=6, dec=0,
    thresholds=[{"value":None,"color":GREEN},{"value":1,"color":RED}]))
P.append(stat("文件权限错误", safe_q("file_permission_error"), 3,y, w=3,h=6, dec=0,
    thresholds=[{"value":None,"color":GREEN},{"value":1,"color":RED}]))
P.append(stat("文件不存在", safe_q("file_not_found_error"), 6,y, w=3,h=6, dec=0,
    thresholds=[{"value":None,"color":GREEN},{"value":1,"color":RED}]))
P.append(stat("文件stat失败", safe_q("file_stat_error"), 9,y, w=3,h=6, dec=0,
    thresholds=[{"value":None,"color":GREEN},{"value":1,"color":RED}]))
P.append(stat("fd耗尽错误", safe_q("file_open_limit_error"), 12,y, w=3,h=6, dec=0,
    thresholds=[{"value":None,"color":GREEN},{"value":1,"color":RED}]))
P.append(stat("进程退出码", safe_q("process_stop_code"), 15,y, w=3,h=6, dec=0))
P.append(stat("配置加载成功", rate_q("config_reload_success_count"), 18,y, w=3,h=6, unit="cps",dec=2))
P.append(stat("配置加载失败", rate_q("config_reload_failure_count"), 21,y, w=3,h=6, unit="cps",dec=2,
    thresholds=[{"value":None,"color":GREEN},{"value":0.01,"color":RED}]))
y+=6

P.append(ts("告警趋势",[safe_q("loglistener_alarm_alarm_count")], 0,y, w=24,h=6))
y+=6

# ===== Section 6: 资源水位 =====
P.append(row_panel("💻 LogListener 资源水位", y)); y+=1

P.append(gauge("CPU使用率", safe_q("loglistener_cpu_usage"), 0,y))
P.append(stat("内存使用", safe_q("loglistener_mem_used"), 4,y, w=4,h=6, unit="decbytes",dec=1))
P.append(stat("打开文件数", safe_q("total_open_files"), 8,y, w=4,h=6, dec=0,
    thresholds=[{"value":None,"color":GREEN},{"value":5000,"color":YELLOW},{"value":10000,"color":RED}]))
P.append(stat("监控目录数", safe_q("total_monitor_dirs"), 12,y, w=4,h=6, dec=0))
P.append(stat("采集配置数", safe_q("total_log_configs"), 16,y, w=4,h=6, dec=0))
P.append(stat("进程重启次数", safe_q("process_restart_times"), 20,y, w=4,h=6, dec=0,
    thresholds=[{"value":None,"color":GREEN},{"value":1,"color":YELLOW},{"value":5,"color":RED}]))
y+=6

P.append(ts("CPU 使用率趋势", safe_q("loglistener_cpu_usage"), 0,y, w=12,h=7, unit="%",
    thresholds=[{"value":None,"color":GREEN},{"value":50,"color":YELLOW},{"value":80,"color":RED}], th_style="area"))
P.append(ts("内存使用趋势", safe_q("loglistener_mem_used"), 12,y, w=12,h=7, unit="decbytes"))
y+=7

# ===== Section 7: 宿主机系统 =====
P.append(row_panel("🖥️ 宿主机系统资源", y)); y+=1

P.append(gauge("系统CPU%", safe_q("system_cpu_usage"), 0,y))
P.append(gauge("系统内存%", safe_q("system_mem_util"), 4,y))
P.append(stat("已用内存", safe_q("system_mem_used"), 8,y, w=4,h=6, unit="decbytes",dec=1))
P.append(stat("可用内存", safe_q("system_mem_available"), 12,y, w=4,h=6, unit="decbytes",dec=1))
P.append(stat("内存总量", safe_q("system_mem_usage"), 16,y, w=4,h=6, unit="decbytes",dec=1))
P.append(stat("磁盘使用率", safe_q("system_disk_usage_percent"), 20,y, w=4,h=6, unit="%",dec=1,
    thresholds=[{"value":None,"color":GREEN},{"value":70,"color":YELLOW},{"value":90,"color":RED}]))
y+=6

# ========== ASSEMBLE ==========
dashboard = {
    "panels": P,
    "templating": {
        "list": [{
            "name":"IP","label":"实例IP","type":"custom","default":[],
            "staticOptions":[],"datasource":{"datasource":None,"regionId":RID,"TopicId":TID},
            "dynamicEnable":True,"topicType":"metric","metric":"loglistener_cpu_usage",
            "qryType":"value","labelFilters":[],"metricLabel":"IP"
        }],
        "tagFilters":[{"name":"tag-filter","label":"","type":"tagFilter","default":None,"current":[]}]
    },
    "time":["now-1h","now"],
    "timezone":"browser"
}

data_str = json.dumps(dashboard, ensure_ascii=False, separators=(',',':'))
print(f"Panels: {len(P)}")
print(f"JSON size: {len(data_str)} chars")

# 保存
with open("/tmp/ll_dashboard_data.json","w") as f:
    f.write(data_str)
print("Saved to /tmp/ll_dashboard_data.json")
