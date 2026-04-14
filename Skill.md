# CLS CLI — AI Agent Skill

> 让 AI Agent 通过命令行操控腾讯云日志服务 (CLS)：日志检索、告警管理、采集配置、仪表盘……用自然语言即可完成。

## 前置条件

- macOS / Linux
- Go 1.23+（用于编译安装）
- 腾讯云账号的 SecretId 和 SecretKey（[API密钥管理](https://console.cloud.tencent.com/cam/capi)）

## 安装

```bash
# 1. 克隆仓库
git clone https://github.com/trumphuang/CLS_CLI.git
cd CLS_CLI/cls-cli

# 2. 编译
go build -o cls-cli .

# 3. 安装到系统路径
sudo mv cls-cli /usr/local/bin/

# 4. 验证安装
cls-cli version
```

## 初始化配置

```bash
# 交互式配置（会提示输入）
cls-cli config init

# 或一行搞定
cls-cli config init \
  --secret-id <YOUR_SECRET_ID> \
  --secret-key <YOUR_SECRET_KEY> \
  --region ap-guangzhou
```

配置保存在 `~/.cls-cli/config.json`，也支持环境变量：

```bash
export TENCENTCLOUD_SECRET_ID=xxx
export TENCENTCLOUD_SECRET_KEY=xxx
export CLS_DEFAULT_REGION=ap-guangzhou
```

## 升级

```bash
cls-cli upgrade
```

## 命令速查

### 全局参数

| 参数 | 说明 |
|---|---|
| `--region <region>` | 指定地域，优先级最高，覆盖配置文件和环境变量 |
| `--format json\|pretty\|table\|csv` | 输出格式 |
| `--dry-run` | 预览模式，不实际执行 |
| `-y, --yes` | 跳过危险操作的二次确认 |

### 日志检索 (`log`)

```bash
# 搜索日志
cls-cli log +search --topic-id <topic_id> --query "level:ERROR" --from "1 hour ago"

# 查看日志上下文
cls-cli log +context --topic-id <topic_id> --pkg-id <pkg_id> --pkg-log-id <pkg_log_id>

# 实时 tail
cls-cli log +tail --topic-id <topic_id> --query "*"

# 日志直方图
cls-cli log +histogram --topic-id <topic_id> --query "*" --from "1 hour ago"

# 下载日志
cls-cli log +download --topic-id <topic_id> --query "*" --from "1 hour ago" --output logs.json
```

### 日志主题 (`topic`)

```bash
cls-cli topic +list                                    # 列出主题
cls-cli topic +list --region ap-beijing                # 指定地域
cls-cli topic +create --logset <id> --name "my-topic"  # 创建主题
cls-cli topic +info --topic <topic_id>                 # 主题详情
cls-cli topic +delete --topic <topic_id>               # 删除主题
cls-cli topic +logsets                                 # 列出日志集
```

### 告警管理 (`alarm`)

```bash
cls-cli alarm +list                                # 列出告警策略
cls-cli alarm +history --from "7 days ago"         # 告警历史
cls-cli alarm +create --name "Error Alert" \
  --topic <topic_id> \
  --query "level:ERROR | SELECT COUNT(*) as cnt" \
  --condition '$1.cnt > 100' --period 5            # 创建告警
cls-cli alarm +delete --alarm-id <id>              # 删除告警
cls-cli alarm +notices                             # 列出通知渠道
```

### 仪表盘 (`dashboard` / `dash`)

```bash
cls-cli dashboard +list                            # 列出仪表盘
cls-cli dash +list --name "运维总览"                # 按名称过滤
cls-cli dash +info --id <dashboard_id>             # 仪表盘详情
cls-cli dash +create --name "新仪表盘"              # 创建
cls-cli dash +update --id <id> --name "新名称"      # 修改
cls-cli dash +delete --id <id>                     # 删除
```

### 机器组 (`machinegroup` / `mg`)

```bash
cls-cli machinegroup +list                                              # 列出机器组
cls-cli mg +create --name web --type ip --values "10.0.0.1,10.0.0.2"   # 创建(IP)
cls-cli mg +create --name web --type label --values "webserver"         # 创建(标签)
cls-cli mg +status --id <group_id>                                      # 机器状态
cls-cli mg +info --id <group_id>                                        # 详情
cls-cli mg +delete --id <group_id>                                      # 删除
```

### 采集配置 (`collector` / `col`)

```bash
cls-cli collector +list                                 # 列出采集配置
cls-cli col +create --name "app-logs" \
  --topic <topic_id> --type json \
  --path "/var/log/app" --file-pattern "*.log" \
  --group-id <group_id>                                 # 创建 JSON 采集
cls-cli col +info --id <config_id>                      # 详情
cls-cli col +delete --id <config_id>                    # 删除
cls-cli col +guide                                      # 采集入门指南
```

### LogListener 管理 (`loglistener` / `ll`)

```bash
cls-cli loglistener +install                            # 安装脚本
cls-cli ll +init --region ap-guangzhou                  # 初始化
cls-cli ll +start                                       # 启动
cls-cli ll +stop                                        # 停止
cls-cli ll +restart                                     # 重启
cls-cli ll +status                                      # 状态
cls-cli ll +check                                       # 心跳检查
cls-cli ll +uninstall                                   # 卸载
```

### 通用 API (`api`)

覆盖所有 CLS API 3.0 接口，适用于快捷命令未封装的操作：

```bash
# 调用任意 API
cls-cli api <Action> --params '<JSON>'

# 示例
cls-cli api DescribeIndex --params '{"TopicId":"xxx"}'
cls-cli api CreateIndex --params '{"TopicId":"xxx","Rule":{...}}'
cls-cli api SearchLog --params '{"TopicId":"xxx","Query":"*","From":1700000000000,"To":1700003600000}'
```

## AI Agent 使用指南

当用户用自然语言描述需求时，按以下模式匹配并调用对应命令：

| 用户意图 | 推荐命令 |
|---|---|
| 查日志 / 搜索日志 / 看看有没有错误 | `cls-cli log +search` |
| 查某条日志的上下文 | `cls-cli log +context` |
| 实时看日志 | `cls-cli log +tail` |
| 看看有哪些主题 / topic | `cls-cli topic +list` |
| 创建主题 | `cls-cli topic +create` |
| 看告警 / 最近有没有告警 | `cls-cli alarm +list` + `cls-cli alarm +history` |
| 创建告警规则 | `cls-cli alarm +create` |
| 看仪表盘 | `cls-cli dashboard +list` |
| 机器状态 / 哪些机器离线 | `cls-cli mg +status` |
| 配置日志采集 | `cls-cli col +guide`（先看指南）→ 然后按步骤操作 |
| 切换地域查询 | 在任何命令后加 `--region ap-beijing` |
| 其他高级操作 | `cls-cli api <Action> --params '{...}'` |

## 常见地域代码

| 地域 | 代码 |
|---|---|
| 广州 | `ap-guangzhou` |
| 上海 | `ap-shanghai` |
| 北京 | `ap-beijing` |
| 成都 | `ap-chengdu` |
| 重庆 | `ap-chongqing` |
| 南京 | `ap-nanjing` |
| 香港 | `ap-hongkong` |
| 新加坡 | `ap-singapore` |
| 硅谷 | `na-siliconvalley` |
| 法兰克福 | `eu-frankfurt` |

## 项目信息

- 仓库：https://github.com/trumphuang/CLS_CLI
- 协议：MIT
- 依赖：仅 `cobra`，签名算法自行实现，极简零外部依赖
