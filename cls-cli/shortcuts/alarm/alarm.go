package alarm

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/tencentcloud/cls-cli/internal/cmdutil"
	"github.com/tencentcloud/cls-cli/internal/output"
)

func RegisterShortcuts(rootCmd *cobra.Command, f *cmdutil.Factory) {
	alarmCmd := &cobra.Command{
		Use:   "alarm",
		Short: "告警管理相关命令",
		Long:  "告警域：查看告警策略、告警历史、通知渠道等",
	}

	alarmCmd.AddCommand(newListCmd(f))
	alarmCmd.AddCommand(newHistoryCmd(f))
	alarmCmd.AddCommand(newCreateCmd(f))
	alarmCmd.AddCommand(newDeleteCmd(f))
	alarmCmd.AddCommand(newNoticeListCmd(f))

	rootCmd.AddCommand(alarmCmd)
}

func newListCmd(f *cmdutil.Factory) *cobra.Command {
	var (
		name   string
		offset int64
		limit  int64
	)

	cmd := &cobra.Command{
		Use:   "+list",
		Short: "列出告警策略",
		Long: `列出当前 Region 下的告警策略。

示例:
  cls-cli alarm +list
  cls-cli alarm +list --name "Error Rate" --format table`,
		RunE: func(cmd *cobra.Command, args []string) error {
			clsClient, err := f.CLSClient()
			if err != nil {
				return err
			}

			params := map[string]interface{}{
				"Offset": offset,
				"Limit":  limit,
			}
			if name != "" {
				params["Filters"] = []map[string]interface{}{
					{"Key": "alarmName", "Values": []string{name}},
				}
			}

			result, err := clsClient.Call("DescribeAlarms", params)
			if err != nil {
				return err
			}

			formatAlarmListResult(result, f.Format)
			return nil
		},
	}

	cmd.Flags().StringVar(&name, "name", "", "按告警名称过滤")
	cmd.Flags().Int64Var(&offset, "offset", 0, "偏移量")
	cmd.Flags().Int64Var(&limit, "limit", 20, "返回条数")
	return cmd
}

func newHistoryCmd(f *cmdutil.Factory) *cobra.Command {
	var (
		alarmID string
		topicID string
		offset  int64
		limit   int64
	)

	cmd := &cobra.Command{
		Use:   "+history",
		Short: "查看告警历史记录",
		Long: `查看告警触发历史。

示例:
  cls-cli alarm +history
  cls-cli alarm +history --alarm-id <alarm_id> --format table`,
		RunE: func(cmd *cobra.Command, args []string) error {
			clsClient, err := f.CLSClient()
			if err != nil {
				return err
			}

			params := map[string]interface{}{
				"Offset": offset,
				"Limit":  limit,
			}

			var filters []map[string]interface{}
			if alarmID != "" {
				filters = append(filters, map[string]interface{}{
					"Key":    "alarmId",
					"Values": []string{alarmID},
				})
			}
			if topicID != "" {
				filters = append(filters, map[string]interface{}{
					"Key":    "topicId",
					"Values": []string{topicID},
				})
			}
			if len(filters) > 0 {
				params["Filters"] = filters
			}

			result, err := clsClient.Call("DescribeAlarmNotices", params)
			if err != nil {
				return err
			}

			output.FormatOutput(result, f.Format)
			return nil
		},
	}

	cmd.Flags().StringVar(&alarmID, "alarm-id", "", "按告警策略 ID 过滤")
	cmd.Flags().StringVar(&topicID, "topic", "", "按日志主题 ID 过滤")
	cmd.Flags().Int64Var(&offset, "offset", 0, "偏移量")
	cmd.Flags().Int64Var(&limit, "limit", 20, "返回条数")
	return cmd
}

func newCreateCmd(f *cmdutil.Factory) *cobra.Command {
	var (
		name      string
		topicID   string
		query     string
		condition string
		period    int64
		noticeID  string
	)

	cmd := &cobra.Command{
		Use:   "+create",
		Short: "创建告警策略",
		Long: `创建一个新的告警策略。

示例:
  cls-cli alarm +create --name "Error Alert" --topic <topic_id> \
    --query "level:ERROR | SELECT COUNT(*) as err_count" \
    --condition "$1.err_count > 100" --period 5 --notice <notice_id>`,
		RunE: func(cmd *cobra.Command, args []string) error {
			if name == "" || topicID == "" || query == "" || condition == "" {
				return fmt.Errorf("--name, --topic, --query, --condition 参数必填")
			}

			if f.DryRun {
				fmt.Fprintf(f.IOStreams.Out, "DRY RUN:\n  Action: CreateAlarm\n  Name: %s\n  TopicId: %s\n  Query: %s\n  Condition: %s\n  Period: %d min\n", name, topicID, query, condition, period)
				return nil
			}

			clsClient, err := f.CLSClient()
			if err != nil {
				return err
			}

			params := map[string]interface{}{
				"Name": name,
				"AlarmTargets": []map[string]interface{}{
					{
						"TopicId":         topicID,
						"Query":           query,
						"Number":          1,
						"StartTimeOffset": -period * 60,
						"EndTimeOffset":   0,
						"SyntaxRule":      1,
					},
				},
				"MonitorTime": map[string]interface{}{
					"Type": "Period",
					"Time": period,
				},
				"TriggerCount": 1,
				"AlarmPeriod":  15,
				"Condition":    condition,
				"Status":       true,
			}
			if noticeID != "" {
				params["AlarmNoticeIds"] = []string{noticeID}
			}

			result, err := clsClient.Call("CreateAlarm", params)
			if err != nil {
				return err
			}

			output.FormatOutput(result, f.Format)
			output.PrintSuccess("告警策略创建成功")
			return nil
		},
	}

	cmd.Flags().StringVar(&name, "name", "", "告警名称（必填）")
	cmd.Flags().StringVar(&topicID, "topic", "", "日志主题 ID（必填）")
	cmd.Flags().StringVar(&query, "query", "", "检索分析语句（必填）")
	cmd.Flags().StringVar(&condition, "condition", "", "触发条件（必填）")
	cmd.Flags().Int64Var(&period, "period", 5, "监控周期（分钟）")
	cmd.Flags().StringVar(&noticeID, "notice", "", "通知渠道组 ID")
	return cmd
}

func newDeleteCmd(f *cmdutil.Factory) *cobra.Command {
	var alarmID string

	cmd := &cobra.Command{
		Use:   "+delete",
		Short: "删除告警策略",
		Long: `删除指定的告警策略。

示例:
  cls-cli alarm +delete --alarm-id <alarm_id>`,
		RunE: func(cmd *cobra.Command, args []string) error {
			if alarmID == "" {
				return fmt.Errorf("--alarm-id 参数必填")
			}

			if f.DryRun {
				fmt.Fprintf(f.IOStreams.Out, "DRY RUN:\n  Action: DeleteAlarm\n  AlarmId: %s\n", alarmID)
				return nil
			}

			clsClient, err := f.CLSClient()
			if err != nil {
				return err
			}

			params := map[string]interface{}{
				"AlarmId": alarmID,
			}

			_, err = clsClient.Call("DeleteAlarm", params)
			if err != nil {
				return err
			}

			output.PrintSuccess(fmt.Sprintf("告警策略 %s 已删除", alarmID))
			return nil
		},
	}

	cmd.Flags().StringVar(&alarmID, "alarm-id", "", "告警策略 ID（必填）")
	return cmd
}

func newNoticeListCmd(f *cmdutil.Factory) *cobra.Command {
	var (
		offset int64
		limit  int64
	)

	cmd := &cobra.Command{
		Use:   "+notices",
		Short: "列出通知渠道组",
		Long: `列出当前 Region 下的告警通知渠道组。

示例:
  cls-cli alarm +notices
  cls-cli alarm +notices --format table`,
		RunE: func(cmd *cobra.Command, args []string) error {
			clsClient, err := f.CLSClient()
			if err != nil {
				return err
			}

			params := map[string]interface{}{
				"Offset": offset,
				"Limit":  limit,
			}

			result, err := clsClient.Call("DescribeAlarmNotices", params)
			if err != nil {
				return err
			}

			output.FormatOutput(result, f.Format)
			return nil
		},
	}

	cmd.Flags().Int64Var(&offset, "offset", 0, "偏移量")
	cmd.Flags().Int64Var(&limit, "limit", 20, "返回条数")
	return cmd
}

func formatAlarmListResult(data interface{}, format output.Format) {
	if format == output.FormatTable || format == output.FormatCSV {
		dataMap, ok := data.(map[string]interface{})
		if !ok {
			output.FormatOutput(data, format)
			return
		}
		resp, ok := dataMap["Response"].(map[string]interface{})
		if !ok {
			output.FormatOutput(data, format)
			return
		}
		if alarms, ok := resp["Alarms"].([]interface{}); ok {
			rows := make([]interface{}, 0, len(alarms))
			for _, a := range alarms {
				if m, ok := a.(map[string]interface{}); ok {
					rows = append(rows, map[string]interface{}{
						"AlarmId":    m["AlarmId"],
						"Name":       m["Name"],
						"Status":     m["Status"],
						"Condition":  m["Condition"],
						"CreateTime": m["CreateTime"],
					})
				}
			}
			output.FormatOutput(rows, format)
			return
		}
	}
	output.FormatOutput(data, format)
}

