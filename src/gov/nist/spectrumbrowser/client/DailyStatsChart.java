/*
* Conditions Of Use 
* 
* This software was developed by employees of the National Institute of
* Standards and Technology (NIST), and others. 
* This software has been contributed to the public domain. 
* Pursuant to title 15 Untied States Code Section 105, works of NIST
* employees are not subject to copyright protection in the United States
* and are considered to be in the public domain. 
* As a result, a formal license is not needed to use this software.
* 
* This software is provided "AS IS."  
* NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
* OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
* AND DATA ACCURACY.  NIST does not warrant or make any representations
* regarding the use of the software or the results thereof, including but
* not limited to the correctness, accuracy, reliability or usefulness of
* this software.
*/
package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserScreen;
import gov.nist.spectrumbrowser.common.Defines;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.JsArray;
import com.google.gwt.core.client.JsDate;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HasVerticalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;
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
import com.googlecode.gwt.charts.client.options.Gridlines;
import com.googlecode.gwt.charts.client.options.HAxis;
import com.googlecode.gwt.charts.client.options.VAxis;
import com.reveregroup.gwt.imagepreloader.FitImage;
import com.reveregroup.gwt.imagepreloader.ImageLoadEvent;
import com.reveregroup.gwt.imagepreloader.ImageLoadHandler;
import com.reveregroup.gwt.imagepreloader.ImagePreloader;

public class DailyStatsChart extends AbstractSpectrumBrowserScreen implements
		SpectrumBrowserCallback<String> {

	public static final String END_LABEL = "Daily Occupancy";
	public static final String LABEL = END_LABEL + ">>";

	private SpectrumBrowser spectrumBrowser;
	private VerticalPanel verticalPanel;
	private LineChart lineChart;
	private HorizontalPanel horizontalPanel;
	private Label helpLabel;
	private long mMinTime;
	private String mMeasurementType;
	private String mSensorId;
	private HashMap<Integer, DailyStat> selectionProperties = new HashMap<Integer, DailyStat>();
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
	private ArrayList<SpectrumBrowserScreen> navigation;
	private SpectrumBrowserShowDatasets spectrumBrowserShowDatasets;
	private double lat;
	private double lon;
	private double alt;
	
	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	class DailyStat {
		String sensorId;
		long startTime;
		String mType;
		long count;
		float maxOccpancy;
		float minOccupancy;
		float meanOccupancy;
		float medianOccupancy;

		public DailyStat(String sensorId, long startTime, String mType,
				long count, float max, float min, float mean) {
			this.sensorId = sensorId;
			this.startTime = startTime;
			this.mType = mType;
			this.count = count;
			this.maxOccpancy = max;
			this.minOccupancy = min;
			this.meanOccupancy = mean;
			
			
			
		}

		public void setMedianOccupancy(float median) {
			medianOccupancy = median;
		}
	}

	public DailyStatsChart(SpectrumBrowser spectrumBrowser,
			SpectrumBrowserShowDatasets spectrumBrowserShowDatasets,
			ArrayList<SpectrumBrowserScreen> navigation, String sensorId,
			double latitude, double longitude, double altitude,
			long minTime, int days, String sys2detect, long minFreq,
			long maxFreq, long subBandMinFreq, long subBandMaxFreq,
			String measurementType, VerticalPanel verticalPanel) {

		super.setNavigation(verticalPanel, navigation, spectrumBrowser,
				END_LABEL);

		this.lat = latitude;
		this.lon = longitude;
		this.alt = altitude;
		this.navigation = new ArrayList<SpectrumBrowserScreen>(navigation);
		this.navigation.add(this);
		this.spectrumBrowserShowDatasets = spectrumBrowserShowDatasets;
		this.spectrumBrowser = spectrumBrowser;
		this.verticalPanel = verticalPanel;
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
		spectrumBrowserShowDatasets.freeze();
		spectrumBrowser.getSpectrumBrowserService().getDailyMaxMinMeanStats(
				sensorId, latitude, longitude, altitude, minTime, days, sys2detect, minFreq, maxFreq,
				mSubBandMinFreq, mSubBandMaxFreq, this);

	}

	@Override
	public void onSuccess(String result) {
		try {
		
			jsonValue = JSONParser.parseLenient(result);
			logger.finer(result);
			String status = jsonValue.isObject().get(Defines.STATUS).isString()
					.stringValue();
			if (status.equals(Defines.OK)) {
				mMinTime = (long) jsonValue.isObject().get("tmin").isNumber()
						.doubleValue();
				prevMinTime = (long) jsonValue.isObject().get("prevTmin")
						.isNumber().doubleValue();
				nextMinTime = (long) jsonValue.isObject().get("nextTmin")
						.isNumber().doubleValue();
				draw();
			} else {
				Window.alert("Error Processing Request : " 
						+ jsonValue.isObject().get(Defines.ERROR_MESSAGE).isString().stringValue());
				spectrumBrowserShowDatasets.unFreeze();
			}
		} catch (Exception ex) {
			logger.log(Level.SEVERE, "Error in processing result ", ex);
			spectrumBrowser.logoff();
		}
	}

	public void draw() {
		ChartLoader chartLoader = new ChartLoader(ChartPackage.CORECHART);

		try {
			chartLoader.loadApi(new Runnable() {
				@Override
				public void run() {
					buttonGrid = new Grid(1, 2);
					horizontalPanel = new HorizontalPanel();
					horizontalPanel.setWidth(SpectrumBrowser.SPEC_WIDTH + "px");
					horizontalPanel.setHeight(SpectrumBrowser.SPEC_HEIGHT + "px");
					lineChart = new LineChart();
					horizontalPanel.add(lineChart);
				    verticalPanel.clear();
					//waitImage.setVisible(false);
					drawNavigation();
					String startDate = jsonValue.isObject().get("startDate")
							.isString().stringValue();
					HTML title = new HTML("<h2>" + END_LABEL + "</h2>");

					verticalPanel.add(title);
				
					
					

					double fmin = jsonValue.isObject().get("minFreq")
							.isNumber().doubleValue() / 1E6;
					double fmax = jsonValue.isObject().get("maxFreq")
							.isNumber().doubleValue() / 1E6;
					int nchannels = (int) jsonValue.isObject()
							.get(Defines.CHANNEL_COUNT).isNumber()
							.doubleValue();
					int cutoff = (int) jsonValue.isObject().get("cutoff")
							.isNumber().doubleValue();

					HTML infoTitle = new HTML("<h3>Start Date= " + startDate
							+ ";Detected System = " + sys2detect
							+ "; minFreq = " + fmin + " MHz; maxFreq = " + fmax
							+ " MHz" + "; channelCount = " + nchannels
							+ "; Occupancy Threshold = " + cutoff
							+ " dBm </h3>");
					verticalPanel.add(infoTitle);
					String helpText = " Click on a point to see detail.";
					helpLabel = new Label();
					helpLabel.setText(helpText);
					verticalPanel.add(helpLabel);
					verticalPanel.add(buttonGrid);
					int buttonCount = 0;
					if (prevMinTime < mMinTime) {
						Button prevIntervalButton = new Button("<< Previous "
								+ days + " Days");
						prevIntervalButton
								.setTitle("Click to see previous interval");
						buttonGrid.setWidget(0, 0, prevIntervalButton);
						verticalPanel.add(buttonGrid);
						buttonCount++;
						prevIntervalButton.addClickHandler(new ClickHandler() {
							@Override
							public void onClick(ClickEvent event) {
								mMinTime = prevMinTime;
								helpLabel
										.setText("Computing Occupancy please wait");
								spectrumBrowser.showWaitImage();
								spectrumBrowser.getSpectrumBrowserService()
										.getDailyMaxMinMeanStats(mSensorId,
												lat,lon,alt,
												mMinTime, days, sys2detect,
												mMinFreq, mMaxFreq,
												mSubBandMinFreq,
												mSubBandMaxFreq,
												DailyStatsChart.this);
							}

						});
					}

					if (nextMinTime > mMinTime) {
						Button nextIntervalButton = new Button("Next " + days
								+ " Days >>");
						nextIntervalButton
								.setTitle("Click to see next interval");
						buttonGrid.setWidget(0, 1, nextIntervalButton);
						buttonCount++;

						nextIntervalButton.addClickHandler(new ClickHandler() {

							@Override
							public void onClick(ClickEvent event) {
								mMinTime = nextMinTime;
								spectrumBrowser.showWaitImage();
								helpLabel
										.setText("Computing Occupancy please wait");
								spectrumBrowser.getSpectrumBrowserService()
										.getDailyMaxMinMeanStats(mSensorId,
												lat,lon,alt,
												mMinTime, days, sys2detect,
												mMinFreq, mMaxFreq,
												mSubBandMinFreq,
												mSubBandMaxFreq,
												DailyStatsChart.this);
							}

						});
					}

					if (buttonCount != 0) {
						buttonGrid.setStyleName("selectionGrid");
					}
					for (int i = 0; i < buttonGrid.getRowCount(); i++) {
						for (int j = 0; j < buttonGrid.getColumnCount(); j++) {
							buttonGrid.getCellFormatter().setHorizontalAlignment(i, j,
									HasHorizontalAlignment.ALIGN_CENTER);
							buttonGrid.getCellFormatter().setVerticalAlignment(i, j,
									HasVerticalAlignment.ALIGN_MIDDLE);
						}
					}

					verticalPanel.add(horizontalPanel);
					DataTable dataTable = DataTable.create();
					dataTable.addColumn(ColumnType.NUMBER, " Days");
					dataTable.addColumn(ColumnType.NUMBER, " Min");
					dataTable.addColumn(ColumnType.NUMBER, " Max");
					dataTable.addColumn(ColumnType.NUMBER, " Mean");
					/* if (mMeasurementType.equals("Swept-frequency")) {
						dataTable.addColumn(ColumnType.NUMBER, " Median");
					}*/

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
									spectrumBrowser.showWaitImage();
									spectrumBrowser.showWaitImage();
									
									new FftPowerOneDayOccupancyChart(
											spectrumBrowser, navigation,
											mSensorId, lat, lon, alt, ds.startTime,
											sys2detect, mMinFreq, mMaxFreq,
											verticalPanel);
								} else {
									spectrumBrowser.showWaitImage();
									new SweptFrequencyOneDaySpectrogramChart(
											mSensorId, lat, lon, alt, ds.startTime,
											sys2detect, mMinFreq, mMaxFreq,
											mSubBandMinFreq, mSubBandMaxFreq,
											verticalPanel, spectrumBrowser,
											navigation);

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
							long count = (long) statsObject.get("count")
									.isNumber().doubleValue();
							int dayOffset = Integer.parseInt(dayString) / 24;
							long time = (long) statsObject
									.get("dayBoundaryTimeStamp").isNumber()
									.doubleValue();

							DailyStat dailyStat = new DailyStat(mSensorId,
									time, mMeasurementType, count, round2(max),
									round2(min), round2(mean));
							selectionProperties.put(rowIndex, dailyStat);

							dataTable.setCell(rowIndex, 0, dayOffset, count
									+ " acquisitions ; " + dayOffset
									+ " days from start");
							dataTable.setCell(rowIndex, 1, round2(min),
									round2(min) + "%");
							dataTable.setCell(rowIndex, 2, round2(max),
									round2(max) + "%");
							dataTable.setCell(rowIndex, 3, round2(mean),
									round2(mean) + "%");
							/* if (statsObject.containsKey("medianOccupancy") ) {
								double median = statsObject
										.get("medianOccupancy").isNumber()
										.doubleValue() * 100;
								dataTable.setCell(rowIndex, 4, round2(median),
										round2(median) + "%");
								dailyStat.setMedianOccupancy(round2(median));
							} */
							rowIndex++;
						}
					} catch (Throwable ex) {
						logger.log(Level.SEVERE, "problem generating chart ",
								ex);
					}
					LineChartOptions options = LineChartOptions.create();
					options.setBackgroundColor("#f0f0f0");
					options.setPointSize(5);
					HAxis haxis = HAxis.create("Days from start date.");
					Gridlines gridLines = Gridlines.create();
					gridLines.setCount(days);
					haxis.setGridlines(gridLines);
					haxis.setMaxValue(days - 1);
					haxis.setMinValue(0);

					if (days < 10) {
						haxis.setShowTextEvery(1);
					} else if (days < 20) {
						haxis.setShowTextEvery(2);
					} else {
						haxis.setShowTextEvery(4);
					}

					options.setHAxis(haxis);
					options.setVAxis(VAxis.create("Occupancy %"));
					lineChart.setTitle("Click on data point to see detail");

					lineChart.draw(dataTable, options);
					lineChart.setVisible(true);
					lineChart.setHeight(SpectrumBrowser.SPEC_HEIGHT + "px");
					lineChart.setWidth(SpectrumBrowser.SPEC_WIDTH + "px");
					/* override with style if it exists */
					lineChart.setStyleName("lineChart");
					spectrumBrowserShowDatasets.unFreeze();
					spectrumBrowser.hideWaitImage();
				}
			});
		} catch (Throwable ex) {
			logger.log(Level.SEVERE, "Error in processing result ", ex);
			spectrumBrowser.logoff();
		}
	}

	@Override
	public void onFailure(Throwable throwable) {
		logger.log(Level.SEVERE,
				"DailyStatisticsChart : Failure communicating with server ",
				throwable);
		spectrumBrowser.logoff();
	}

}
