package gov.nist.spectrumbrowser.client;

import java.util.Date;
import java.util.HashMap;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.JsArray;
import com.google.gwt.core.client.Scheduler;
import com.google.gwt.i18n.client.DateTimeFormat;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.RootPanel;
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

public class DailyStatsChart implements SpectrumBrowserCallback<String> {

	private SpectrumBrowser spectrumBrowser;
	private VerticalPanel verticalPanel;
	private LineChart lineChart;
	private HorizontalPanel horizontalPanel;
	private String mTitle;
	private int mWidth;
	private int mHeight;
	private long mMinTime;
	private String mMeasurementType;
	private String mSensorId;
	private HashMap<Integer, DailyStat> selectionProperties = new HashMap<Integer, DailyStat>();
	private SpectrumBrowserShowDatasets spectrumBrowserShowDatasets;
	private JSONValue jsonValue;
	private long mUtcOffset;

	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	private static final int SECONDS_PER_DAY = 24 * 60 * 60;

	class DailyStat {
		String sensorId;
		long startTime;
		String mType;

		public DailyStat(String sensorId, long startTime, String mType) {
			this.sensorId = sensorId;
			this.startTime = startTime;
			this.mType = mType;
		}
	}

	public DailyStatsChart(SpectrumBrowser spectrumBrowser,
			SpectrumBrowserShowDatasets spectrumBrowserShowDatasets,
			String sensorId, String timeZoneId, long minTime, long utcOffset, int days, String measurementType,
			VerticalPanel verticalPanel, String title, int width, int height) {
		long maxTime = days * SECONDS_PER_DAY + minTime;
		this.spectrumBrowser = spectrumBrowser;
		this.verticalPanel = verticalPanel;
		mWidth = width;
		mHeight = height;
		mMinTime = minTime;
		mMeasurementType = measurementType;
		mSensorId = sensorId;
		mUtcOffset = utcOffset;
		this.spectrumBrowserShowDatasets = spectrumBrowserShowDatasets;

		mTitle = title;

		spectrumBrowser.getSpectrumBrowserService().getDailyMaxMinMeanStats(
				spectrumBrowser.getSessionId(), sensorId, mUtcOffset, minTime, maxTime,
				this);

	}

	@Override
	public void onSuccess(String result) {
		try {
			jsonValue = JSONParser.parseLenient(result);
			draw();
		} catch (Exception ex) {
			logger.log(Level.SEVERE, "Error in processing result ", ex);
		}
	}

	public void draw() {
		ChartLoader chartLoader = new ChartLoader(ChartPackage.CORECHART);

		try {
			chartLoader.loadApi(new Runnable() {
				@Override
				public void run() {
					horizontalPanel = new HorizontalPanel();
					horizontalPanel.setWidth(mWidth + "px");
					horizontalPanel.setHeight(mHeight + "px");

					lineChart = new LineChart();
					horizontalPanel.add(lineChart);
					verticalPanel.clear();
					MenuBar menuBar = new MenuBar();
					SafeHtmlBuilder safeHtml = new SafeHtmlBuilder();
					
					menuBar.addItem(safeHtml.appendEscaped("Log Off").toSafeHtml(), new Scheduler.ScheduledCommand() {

						@Override
						public void execute() {
							spectrumBrowser.logoff();

						}
					});
					
					menuBar.addItem(new SafeHtmlBuilder().appendEscaped("Select Data Set").toSafeHtml(),
							new Scheduler.ScheduledCommand() {

						@Override
						public void execute() {
							spectrumBrowserShowDatasets.buildUi();
						}});
					
					menuBar.addItem(new SafeHtmlBuilder().appendEscaped("About").toSafeHtml(), new Scheduler.ScheduledCommand() {

						@Override
						public void execute() {
							
						}} );
					
					menuBar.addItem(new SafeHtmlBuilder().appendEscaped("Help").toSafeHtml(), new Scheduler.ScheduledCommand() {
						
						@Override
						public void execute() {
							// TODO Auto-generated method stub
							
						}
					});
					
					verticalPanel.add(menuBar);
					
					HTML title = new HTML(mTitle);
					
					
					verticalPanel.add(title);
					
					verticalPanel.add(horizontalPanel);
					DataTable dataTable = DataTable.create();
					dataTable.addColumn(ColumnType.NUMBER, " Days");
					dataTable.addColumn(ColumnType.NUMBER, " Min Occupancy %");
					dataTable.addColumn(ColumnType.NUMBER, " Max Occupancy %");
					dataTable.addColumn(ColumnType.NUMBER, " Mean Occupancy %");
					lineChart.addSelectHandler(new SelectHandler() {
						@Override
						public void onSelect(SelectEvent event) {
							JsArray<Selection> selections = lineChart
									.getSelection();
							int length = selections.length();
							for (int i = 0; i < length; i++) {
								Selection selection = selections.get(i);
								logger.finer("Selected Row : "
										+ selection.getRow());
								logger.finer("selected col : "
										+ selection.getColumn());
								// If the measurement type is of type FFT-Power
								// then drill down.
								DailyStat ds = selectionProperties
										.get(selection.getRow());
								if (ds.mType.equals("FFT-Power")) {
									DateTimeFormat dtf = DateTimeFormat.getFormat("YYYY MM DD");
									String date = dtf.format( new Date(ds.startTime));
									String title = "Occupancy data for " + date;
									new OneDayOccupancyChart(spectrumBrowser,
											spectrumBrowserShowDatasets, DailyStatsChart.this,
											mSensorId, ds.startTime, mUtcOffset,
											verticalPanel, title, mWidth,
											mHeight);
								}
							}

						}
					});

					JSONObject jsonObject = jsonValue.isObject();
					int dayCount = jsonObject.size();
					logger.finer("dayCount " + dayCount);
					dataTable.addRows(dayCount);
					try {
						for (String dayString : jsonObject.keySet()) {
							JSONObject statsObject = jsonObject.get(dayString)
									.isObject();
							double mean = statsObject.get("meanOccupancy")
									.isNumber().doubleValue() * 100;

							double max = statsObject.get("maxOccupancy")
									.isNumber().doubleValue() * 100;
							double min = statsObject.get("minOccupancy")
									.isNumber().doubleValue() * 100;
							int rowIndex = Integer.parseInt(dayString);
							long time = mMinTime + rowIndex * SECONDS_PER_DAY;

							DailyStat dailyStat = new DailyStat(
									mSensorId, time, mMeasurementType);
							selectionProperties.put(rowIndex, dailyStat);

							dataTable.setValue(rowIndex, 0, rowIndex);
							dataTable.setValue(rowIndex, 1, min);
							dataTable.setValue(rowIndex, 2, max);
							dataTable.setValue(rowIndex, 3, mean);

						}
					} catch (Throwable ex) {
						logger.log(Level.SEVERE, "problem generating chart ",
								ex);
					}
					LineChartOptions options = LineChartOptions.create();
					options.setBackgroundColor("#f0f0f0");
					options.setHAxis(HAxis.create("24 Hour intervals from start date."));
					options.setVAxis(VAxis.create("Channel Occupancy %"));
					lineChart.draw(dataTable, options);
					lineChart.setVisible(true);
					lineChart.setHeight(mHeight + "px");
					lineChart.setWidth(mWidth + "px");
					/* override with style if it exists */
					lineChart.setStyleName("lineChart");
				}
			});
		} catch (Throwable ex) {
			logger.log(Level.SEVERE, "Error in processing result ", ex);
		}
	}

	@Override
	public void onFailure(Throwable throwable) {
		logger.log(Level.SEVERE,
				"DailyStatisticsChart : Failure communicating with server ",
				throwable);
	}

}
