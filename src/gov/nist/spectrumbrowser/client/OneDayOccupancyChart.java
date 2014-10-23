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

public class OneDayOccupancyChart implements SpectrumBrowserCallback<String>, SpectrumBrowserScreen {
	public static final String END_LABEL = "One-day Occupancy";
	public static String LABEL = END_LABEL + ">>";
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
	private HashMap<Integer, SelectionProperty> selectionProperties = new HashMap<Integer, SelectionProperty>();
	private String mTimeZoneId;
	private long mMinFreq;
	private long mMaxFreq;
	private String sys2detect;

	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	class SelectionProperty {
		long selectionTime;

		SelectionProperty(long time) {
			selectionTime = time;
		}
	}


	public OneDayOccupancyChart(SpectrumBrowser spectrumBrowser,
			SpectrumBrowserShowDatasets spectrumBrowserShowDatasets,
			DailyStatsChart dailyStatsChart, String sensorId, long startTime,
			String sys2detect, long minFreq, long maxFreq,
		    VerticalPanel verticalPanel, 
			int width, int height) {
		mStartTime = startTime;
		mSensorId = sensorId;
		mVerticalPanel = verticalPanel;
		mWidth = width;
		mHeight = height;
		mSpectrumBrowser = spectrumBrowser;
		mSpectrumBrowserShowDatasets = spectrumBrowserShowDatasets;
		mDailyStatsChart = dailyStatsChart;
		String sessionId = spectrumBrowser.getSessionId();
		this.sys2detect = sys2detect;
		mMinFreq = minFreq;
		mMaxFreq = maxFreq;
		mSpectrumBrowser.getSpectrumBrowserService().getOneDayStats(sessionId,
				sensorId,  startTime, sys2detect, minFreq, maxFreq, this);
		

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
	
	private float round(double val) {
		return (float)((int)(val*100)/100.0);
	}
	
	public String getLabel() {
		return LABEL;
	}
	
	public String getEndLabel() {
		return END_LABEL;
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

				menuBar.addItem(safeHtml.appendEscaped(SpectrumBrowser.LOGOFF_LABEL).toSafeHtml(),
						new Scheduler.ScheduledCommand() {

							@Override
							public void execute() {
								mSpectrumBrowser.logoff();
							}
						});

				menuBar.addItem(
						new SafeHtmlBuilder().appendEscaped(SpectrumBrowserShowDatasets.LABEL)
								.toSafeHtml(),
						new Scheduler.ScheduledCommand() {

							@Override
							public void execute() {
								mSpectrumBrowserShowDatasets.draw();
							}
						});

				menuBar.addItem(
						new SafeHtmlBuilder().appendEscaped(DailyStatsChart.END_LABEL)
								.toSafeHtml(),
						new Scheduler.ScheduledCommand() {

							@Override
							public void execute() {
								mDailyStatsChart.draw();
							}
						});
				
				menuBar.addItem(new SafeHtmlBuilder().appendEscaped(SpectrumBrowser.ABOUT_LABEL)
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
				mTitle = "One-day Band Occupancy Starting from " + dateString;
				HTML title = new HTML("<H2>" + mTitle + "</H2>");
				mVerticalPanel.add(title);
				int minFreq = (int)((mMinFreq + 500000)/1E6); 
				int maxFreq = (int) ((mMaxFreq + 500000)/1E6); 
				int nChannels = (int)jsonValue.isObject().get("channelCount").isNumber().doubleValue();
				int cutoff = (int) jsonValue.isObject().get("cutoff").isNumber().doubleValue();
				HTML infoTitle = new HTML("<h3>Detected System = " + sys2detect + "; minFreq = " + minFreq + " MHz; maxFreq = " 
				+ maxFreq + " MHz; nChannels = " + nChannels  +  "; Occupancy cutoff = " + cutoff + " dBm </h3>"  );
				mVerticalPanel.add(infoTitle);
				mVerticalPanel.add(horizontalPanel);


				DataTable dataTable = DataTable.create();
				dataTable.addColumn(ColumnType.NUMBER, " Hours since start of day.");
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
						dataTable.setValue(rowIndex, 0, round((double)second/(double)3600));
						dataTable.setValue(rowIndex, 1, round(max));
						dataTable.setValue(rowIndex, 2, round(min));
						dataTable.setValue(rowIndex, 3, round(median));
						dataTable.setValue(rowIndex, 4, round(mean));
						selectionProperties.put(rowIndex,
								new SelectionProperty(time));
						rowIndex++;
					}
					
					lineChart.addSelectHandler(new SelectHandler() {

						@Override
						public void onSelect(SelectEvent event) {
							JsArray<Selection> selections = lineChart.getSelection();
							int length = selections.length();
							for (int i = 0 ; i < length; i ++ ) {
								int row = selections.get(i).getRow();
								SelectionProperty property = selectionProperties.get(row);
								
								new FftPowerOneAcquisitionSpectrogramChart(mSensorId,property.selectionTime, 
										mMinFreq, mMaxFreq,
										mVerticalPanel, mSpectrumBrowser, 
										mSpectrumBrowserShowDatasets, mDailyStatsChart, 
										OneDayOccupancyChart.this, mWidth, mHeight );
							}
						} } );
					LineChartOptions options = LineChartOptions.create();
					options.setBackgroundColor("#f0f0f0");
					options.setPointSize(5);
					lineChart.setHeight(mHeight + "px");
					lineChart.setWidth(mWidth + "px");
					options.setHAxis(HAxis.create("Hours since start of day."));
					options.setVAxis(VAxis.create("Occupancy %"));
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
