package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;

import java.util.HashMap;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.GWT;
import com.google.gwt.core.client.JsArray;
import com.google.gwt.core.client.JsDate;
import com.google.gwt.core.client.Scheduler;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.dom.client.MouseOverEvent;
import com.google.gwt.event.dom.client.MouseOverHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.googlecode.gwt.charts.client.ChartLoader;
import com.googlecode.gwt.charts.client.ChartPackage;
import com.googlecode.gwt.charts.client.ColumnType;
import com.googlecode.gwt.charts.client.DataTable;
import com.googlecode.gwt.charts.client.Selection;
import com.googlecode.gwt.charts.client.corechart.LineChart;
import com.googlecode.gwt.charts.client.corechart.LineChartOptions;
import com.googlecode.gwt.charts.client.event.OnMouseOutEvent;
import com.googlecode.gwt.charts.client.event.OnMouseOutHandler;
import com.googlecode.gwt.charts.client.event.OnMouseOverEvent;
import com.googlecode.gwt.charts.client.event.OnMouseOverHandler;
import com.googlecode.gwt.charts.client.event.SelectEvent;
import com.googlecode.gwt.charts.client.event.SelectHandler;
import com.googlecode.gwt.charts.client.options.HAxis;
import com.googlecode.gwt.charts.client.options.VAxis;

public class DailyStatsChart implements SpectrumBrowserCallback<String>,
		SpectrumBrowserScreen {

	public static final String END_LABEL = "Daily Occupancy";
	public static final String LABEL = END_LABEL + ">>";

	private SpectrumBrowser spectrumBrowser;
	private VerticalPanel verticalPanel;
	private LineChart lineChart;
	private HorizontalPanel horizontalPanel;
	private Label helpLabel;
	private int mWidth;
	private int mHeight;
	private long mMinTime;
	private String mMeasurementType;
	private String mSensorId;
	private HashMap<Integer, DailyStat> selectionProperties = new HashMap<Integer, DailyStat>();
	private SpectrumBrowserShowDatasets spectrumBrowserShowDatasets;
	private JSONValue jsonValue;
	private long mMinFreq;
	private long mMaxFreq;
	private long mSubBandMinFreq;
	private long mSubBandMaxFreq;
	private String sys2detect;
	private Grid buttonGrid;
	private int days;
	private long prevMinTime;
	private long nextMinTime;

	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	class DailyStat {
		String sensorId;
		long startTime;
		String mType;
		long count;

		public DailyStat(String sensorId, long startTime, String mType, long count) {
			this.sensorId = sensorId;
			this.startTime = startTime;
			this.mType = mType;
			this.count = count;
		}
	}

	public String getLabel() {
		return LABEL;
	}

	public String getEndLabel() {
		return END_LABEL;
	}

	public DailyStatsChart(SpectrumBrowser spectrumBrowser,
			SpectrumBrowserShowDatasets spectrumBrowserShowDatasets,
			String sensorId, long minTime, int days, String sys2detect,
			long minFreq, long maxFreq, long subBandMinFreq,
			long subBandMaxFreq, String measurementType,
			VerticalPanel verticalPanel, int width, int height) {
		this.spectrumBrowser = spectrumBrowser;
		this.verticalPanel = verticalPanel;
		mWidth = width;
		mHeight = height;
		mMinFreq = minFreq;
		mMaxFreq = maxFreq;
		mSubBandMinFreq = subBandMinFreq;
		mSubBandMaxFreq = subBandMaxFreq;
		this.sys2detect = sys2detect;
		JsDate jsDate = JsDate.create(minTime * 1000);
		int month = jsDate.getMonth();
		int day = jsDate.getDay();
		int year = jsDate.getFullYear();
		logger.finer("StartDate is " + year + "/" + month + "/" + day);
		mMinTime = minTime;
		mMeasurementType = measurementType;
		mSensorId = sensorId;
		this.days = days;

		this.spectrumBrowserShowDatasets = spectrumBrowserShowDatasets;

		spectrumBrowser.getSpectrumBrowserService().getDailyMaxMinMeanStats(
				spectrumBrowser.getSessionId(), sensorId, minTime, days,
				sys2detect, minFreq, maxFreq, mSubBandMinFreq, mSubBandMaxFreq,
				this);

	}

	@Override
	public void onSuccess(String result) {
		try {
			jsonValue = JSONParser.parseLenient(result);
			logger.finer(result);
			mMinTime = (long) jsonValue.isObject().get("tmin").isNumber()
					.doubleValue();
			prevMinTime = (long) jsonValue.isObject().get("prevTmin")
					.isNumber().doubleValue();
			nextMinTime = (long) jsonValue.isObject().get("nextTmin")
					.isNumber().doubleValue();
			draw();
		} catch (Exception ex) {
			logger.log(Level.SEVERE, "Error in processing result ", ex);
		}
	}

	private float round(double val) {
		return (float) ((int) (val * 100) / 100.0);
	}

	public void draw() {
		ChartLoader chartLoader = new ChartLoader(ChartPackage.CORECHART);

		try {
			chartLoader.loadApi(new Runnable() {
				@Override
				public void run() {
					buttonGrid = new Grid(1, 2);
					horizontalPanel = new HorizontalPanel();
					horizontalPanel.setWidth(mWidth + "px");
					horizontalPanel.setHeight(mHeight + "px");

					lineChart = new LineChart();
					horizontalPanel.add(lineChart);
					verticalPanel.clear();
					MenuBar menuBar = new MenuBar();
					SafeHtmlBuilder safeHtml = new SafeHtmlBuilder();

					menuBar.addItem(
							safeHtml.appendEscaped(SpectrumBrowser.LOGOFF_LABEL)
									.toSafeHtml(),
							new Scheduler.ScheduledCommand() {

								@Override
								public void execute() {
									spectrumBrowser.logoff();

								}
							});

					menuBar.addItem(
							new SafeHtmlBuilder().appendEscaped(
									SpectrumBrowserShowDatasets.END_LABEL)
									.toSafeHtml(),
							new Scheduler.ScheduledCommand() {

								@Override
								public void execute() {
									spectrumBrowserShowDatasets.draw();
								}
							});

					menuBar.addItem(
							new SafeHtmlBuilder().appendEscaped(
									SpectrumBrowser.HELP_LABEL).toSafeHtml(),
							new Scheduler.ScheduledCommand() {

								@Override
								public void execute() {
									// TODO Auto-generated method stub

								}
							});

					verticalPanel.add(menuBar);
					verticalPanel.setTitle("Click on data point to see detail");
					String startDate = jsonValue.isObject().get("startDate")
							.isString().stringValue();
					HTML title = new HTML("<h2>" + END_LABEL + "</h2>");

					verticalPanel.add(title);

					double fmin = jsonValue.isObject().get("minFreq")
							.isNumber().doubleValue() / 1E6;
					double fmax = jsonValue.isObject().get("maxFreq")
							.isNumber().doubleValue() / 1E6;
					int nchannels = (int) jsonValue.isObject()
							.get("channelCount").isNumber().doubleValue();
					int cutoff = (int) jsonValue.isObject().get("cutoff")
							.isNumber().doubleValue();

					HTML infoTitle = new HTML("<h3>Start Date= " + startDate
							+ ";Detected System = " + sys2detect
							+ "; minFreq = " + fmin + " MHz; maxFreq = " + fmax
							+ " MHz" + "; channelCount = " + nchannels
							+ "; Occupancy Threshold = " + cutoff
							+ " dBm </h3>");
					verticalPanel.add(infoTitle);
					verticalPanel.add(buttonGrid);
					Button prevIntervalButton = new Button("<< Previous "
							+ days + " Days");
					prevIntervalButton
							.setTitle("Click to see previous interval");
					buttonGrid.setWidget(0, 0, prevIntervalButton);
					verticalPanel.add(buttonGrid);
					prevIntervalButton.addClickHandler(new ClickHandler() {
						@Override
						public void onClick(ClickEvent event) {
							if (prevMinTime < mMinTime) {
								mMinTime = prevMinTime;
								helpLabel
										.setText("Computing Occupancy please wait");
								spectrumBrowser.getSpectrumBrowserService()
										.getDailyMaxMinMeanStats(
												spectrumBrowser.getSessionId(),
												mSensorId, mMinTime, days,
												sys2detect, mMinFreq, mMaxFreq,
												mSubBandMinFreq,
												mSubBandMaxFreq,
												DailyStatsChart.this);
							}

						}
					});

					Button nextIntervalButton = new Button("Next " + days
							+ " Days >>");
					nextIntervalButton.setTitle("Click to see next interval");
					buttonGrid.setWidget(0, 1, nextIntervalButton);

					nextIntervalButton.addClickHandler(new ClickHandler() {

						@Override
						public void onClick(ClickEvent event) {
							if (nextMinTime > mMinTime) {
								mMinTime = nextMinTime;
								helpLabel
										.setText("Computing Occupancy please wait");
								spectrumBrowser.getSpectrumBrowserService()
										.getDailyMaxMinMeanStats(
												spectrumBrowser.getSessionId(),
												mSensorId, mMinTime, days,
												sys2detect, mMinFreq, mMaxFreq,
												mSubBandMinFreq,
												mSubBandMaxFreq,
												DailyStatsChart.this);
							}
						}
					});

					String helpText = " Click on point to see detail.";
					helpLabel = new Label();
					helpLabel.setText(helpText);
					verticalPanel.add(helpLabel);

					verticalPanel.add(horizontalPanel);
					DataTable dataTable = DataTable.create();
					dataTable.addColumn(ColumnType.NUMBER, " Days");
					dataTable.addColumn(ColumnType.NUMBER, " Min");
					dataTable.addColumn(ColumnType.NUMBER, " Max");
					dataTable.addColumn(ColumnType.NUMBER, " Mean");
					if (mMeasurementType.equals("Swept-frequency")) {
						dataTable.addColumn(ColumnType.NUMBER, " Median");
					}
					
					/* lineChart.addOnMouseOverHandler(new OnMouseOverHandler() {

						@Override
						public void onMouseOver(OnMouseOverEvent event) {
							int row = event.getRow();
							long count = selectionProperties.get(row).count;
							verticalPanel.setTitle("Acquistion Count = " + count);
						}

					});
					
					lineChart.addOnMouseOutHandler(new OnMouseOutHandler() {

						@Override
						public void onMouseOutEvent(OnMouseOutEvent event) {
							verticalPanel.setTitle("Click on point to see detail.");
						}
						
					}); */
					
					
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
									new OneDayOccupancyChart(spectrumBrowser,
											spectrumBrowserShowDatasets,
											DailyStatsChart.this, mSensorId,
											ds.startTime, sys2detect, mMinFreq,
											mMaxFreq, verticalPanel, mWidth,
											mHeight);
								} else {
									logger.finer("mType : " + ds.mType
											+ " drawing one day spectrogram ");

									new SweptFrequencyOneDaySpectrogramChart(
											mSensorId, ds.startTime,
											sys2detect, mMinFreq, mMaxFreq,
											mSubBandMinFreq, mSubBandMaxFreq,
											verticalPanel, spectrumBrowser,
											spectrumBrowserShowDatasets,
											DailyStatsChart.this, mWidth,
											mHeight);

								}
							}

						}
					});

					JSONObject jsonObject = jsonValue.isObject();
					try {
						JSONObject values = jsonObject.get("values").isObject();
						int dayCount = values.size();
						logger.finer("dayCount " + dayCount);
						dataTable.addRows(dayCount);

						int rowIndex = 0;
						for (String dayString : values.keySet()) {
							JSONObject statsObject = values.get(dayString)
									.isObject();
							double mean = statsObject.get("meanOccupancy")
									.isNumber().doubleValue() * 100;
							double max = statsObject.get("maxOccupancy")
									.isNumber().doubleValue() * 100;
							double min = statsObject.get("minOccupancy")
									.isNumber().doubleValue() * 100;
							long count = (long) statsObject.get("count").isNumber().doubleValue();
							int hourOffset = Integer.parseInt(dayString) / 24;
							long time = (long) statsObject
									.get("dayBoundaryTimeStamp").isNumber()
									.doubleValue();

							DailyStat dailyStat = new DailyStat(mSensorId,
									time, mMeasurementType,count);
							selectionProperties.put(rowIndex, dailyStat);

							dataTable.setValue(rowIndex, 0, hourOffset);
							dataTable.setValue(rowIndex, 1, round(min));
							dataTable.setValue(rowIndex, 2, round(max));
							dataTable.setValue(rowIndex, 3, round(mean));
							if (mMeasurementType.equals("Swept-frequency")) {
								double median = statsObject
										.get("medianOccupancy").isNumber()
										.doubleValue() * 100;
								dataTable.setValue(rowIndex, 4, round(median));
							}
							rowIndex++;
						}
					} catch (Throwable ex) {
						logger.log(Level.SEVERE, "problem generating chart ",
								ex);
					}
					LineChartOptions options = LineChartOptions.create();
					options.setBackgroundColor("#f0f0f0");
					options.setPointSize(5);
					options.setHAxis(HAxis.create("Days from start date."));
					options.setVAxis(VAxis.create("Occupancy %"));
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
