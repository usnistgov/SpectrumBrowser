package gov.nist.spectrumbrowser.client;

import java.util.HashMap;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.JsArray;
import com.google.gwt.core.client.Scheduler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.googlecode.gwt.charts.client.ChartLoader;
import com.googlecode.gwt.charts.client.ChartPackage;
import com.googlecode.gwt.charts.client.ColumnType;
import com.googlecode.gwt.charts.client.DataTable;
import com.googlecode.gwt.charts.client.Selection;
import com.googlecode.gwt.charts.client.corechart.LineChart;
import com.googlecode.gwt.charts.client.corechart.LineChartOptions;
import com.googlecode.gwt.charts.client.event.SelectEvent;
import com.googlecode.gwt.charts.client.event.SelectHandler;
import com.googlecode.gwt.charts.client.options.HAxis;
import com.googlecode.gwt.charts.client.options.VAxis;

public class OneDayOccupancyChart implements SpectrumBrowserCallback<String> {
	private long mUtcOffset;
	private long mStartTime;
	private VerticalPanel mVerticalPanel;
	private int mWidth;
	private int mHeight;
	private String mSensorId;
	private String mTitle;
	private SpectrumBrowser mSpectrumBrowser;
	private SpectrumBrowserShowDatasets mSpectrumBrowserShowDatasets;
	private JSONValue jsonValue;
	private HorizontalPanel horizontalPanel;
	private LineChart lineChart;
	private DailyStatsChart mDailyStatsChart;

	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	class SelectionProperty {
		long selectionTime;

		SelectionProperty(long time) {
			selectionTime = time;
		}
	}

	private HashMap<Integer, SelectionProperty> selectionProperties = new HashMap<Integer, SelectionProperty>();
	private String mTimeZoneId;

	public OneDayOccupancyChart(SpectrumBrowser spectrumBrowser,
			SpectrumBrowserShowDatasets spectrumBrowserShowDatasets,
			DailyStatsChart dailyStatsChart, String sensorId, long startTime,
		    VerticalPanel verticalPanel, String title,
			int width, int height) {
		mStartTime = startTime;
		mSensorId = sensorId;
		mVerticalPanel = verticalPanel;
		mWidth = width;
		mHeight = height;
		mTitle = title;
		mSpectrumBrowser = spectrumBrowser;
		mSpectrumBrowserShowDatasets = spectrumBrowserShowDatasets;
		mDailyStatsChart = dailyStatsChart;
		String sessionId = spectrumBrowser.getSessionId();
		mSpectrumBrowser.getSpectrumBrowserService().getOneDayStats(sessionId,
				sensorId,  startTime,  this);

	}

	@Override
	public void onSuccess(String result) {
		try {
			jsonValue = JSONParser.parseLenient(result);
			draw();
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Error in parsing result", th);
		}
	}

	@Override
	public void onFailure(Throwable throwable) {
		logger.log(Level.SEVERE, "Error in contacting server", throwable);
		mSpectrumBrowser.displayError("Problem contacting server");

	}

	public void draw() {
		ChartLoader chartLoader = new ChartLoader(ChartPackage.CORECHART);

		chartLoader.loadApi(new Runnable() {
			@Override
			public void run() {
				mVerticalPanel.clear();
				horizontalPanel = new HorizontalPanel();
				horizontalPanel.setWidth(mWidth + "px");
				horizontalPanel.setHeight(mHeight + "px");

				lineChart = new LineChart();
				horizontalPanel.add(lineChart);
				mVerticalPanel.clear();
				MenuBar menuBar = new MenuBar();
				SafeHtmlBuilder safeHtml = new SafeHtmlBuilder();

				menuBar.addItem(safeHtml.appendEscaped("Log Off").toSafeHtml(),
						new Scheduler.ScheduledCommand() {

							@Override
							public void execute() {
								mSpectrumBrowser.logoff();
							}
						});

				menuBar.addItem(
						new SafeHtmlBuilder().appendEscaped("Select Data Set")
								.toSafeHtml(),
						new Scheduler.ScheduledCommand() {

							@Override
							public void execute() {
								mSpectrumBrowserShowDatasets.buildUi();
							}
						});

				menuBar.addItem(
						new SafeHtmlBuilder().appendEscaped("Daily Stats")
								.toSafeHtml(),
						new Scheduler.ScheduledCommand() {

							@Override
							public void execute() {
								mDailyStatsChart.draw();
							}
						});
				menuBar.addItem(new SafeHtmlBuilder().appendEscaped("About")
						.toSafeHtml(), new Scheduler.ScheduledCommand() {

					@Override
					public void execute() {

					}
				});

				menuBar.addItem(new SafeHtmlBuilder().appendEscaped("Help")
						.toSafeHtml(), new Scheduler.ScheduledCommand() {

					@Override
					public void execute() {

					}
				});
				mVerticalPanel.add(menuBar);
				String dateString = jsonValue.isObject().get("formattedDate").isString().stringValue();
				mTitle = "Occupancy for " + dateString;
				HTML title = new HTML("<H1>" + mTitle + "</H1>");
				mVerticalPanel.add(title);
				mVerticalPanel.add(horizontalPanel);

				DataTable dataTable = DataTable.create();
				dataTable.addColumn(ColumnType.NUMBER, " Seconds since start of day.");
				dataTable.addColumn(ColumnType.NUMBER, " Max Occupancy %");
				dataTable.addColumn(ColumnType.NUMBER, " Min Occupancy %");
				dataTable.addColumn(ColumnType.NUMBER, " Median Occupancy %");
				dataTable.addColumn(ColumnType.NUMBER, " Mean Occupancy %");

				JSONObject jsonObject = jsonValue.isObject().get("values").isObject();
				int rowCount = jsonObject.size();
				logger.finer("rowCount " + rowCount);
				dataTable.addRows(rowCount);
				try {
					int rowIndex = 0;
					for (String secondString : jsonObject.keySet()) {
						JSONObject statsObject = jsonObject.get(secondString)
								.isObject();
						int second = Integer.parseInt(secondString);
						long time = (long) statsObject.get("t").isNumber()
								.doubleValue();
						double mean = statsObject.get("meanOccupancy")
								.isNumber().doubleValue() * 100;
						double max = statsObject.get("maxOccupancy").isNumber()
								.doubleValue() * 100;
						double min = statsObject.get("minOccupancy").isNumber()
								.doubleValue() * 100;
						double median = statsObject.get("medianOccupancy")
								.isNumber().doubleValue() * 100;
						dataTable.setValue(rowIndex, 0, second);
						dataTable.setValue(rowIndex, 1, max);
						dataTable.setValue(rowIndex, 2, min);
						dataTable.setValue(rowIndex, 3, median);
						dataTable.setValue(rowIndex, 4, mean);
						selectionProperties.put(rowIndex,
								new SelectionProperty(time));
						rowIndex++;

					}
					
					lineChart.addSelectHandler(new SelectHandler() {

						@Override
						public void onSelect(SelectEvent event) {
							JsArray<Selection> selections = lineChart.getSelection();
							int length = selections.length();
							logger.finer("Selections.length" + selections.length());
							for (int i = 0 ; i < length; i ++ ) {
								int row = selections.get(i).getRow();
								SelectionProperty property = selectionProperties.get(row);
								
								new OneAcquisitionSpectrogramChart(mSensorId,property.selectionTime, 
										mVerticalPanel, mSpectrumBrowser, 
										mSpectrumBrowserShowDatasets, mDailyStatsChart, 
										OneDayOccupancyChart.this, mWidth, mHeight );
							}
						} } );
					LineChartOptions options = LineChartOptions.create();
					options.setBackgroundColor("#f0f0f0");
					lineChart.setHeight(mHeight + "px");
					lineChart.setWidth(mWidth + "px");
					options.setHAxis(HAxis.create("Seconds since start of day."));
					options.setVAxis(VAxis.create("Channel Occupancy %"));
					lineChart.setStyleName("lineChart");
					lineChart.draw(dataTable, options);
					lineChart.setVisible(true);
				
					horizontalPanel.add(lineChart);
				} catch (Throwable throwable) {
					logger.log(Level.SEVERE, "Problem parsing json ", throwable);
				}
			}
		});

	}

}
