package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

import java.util.ArrayList;
import java.util.Date;
import java.util.HashSet;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.JsDate;
import com.google.gwt.core.client.Scheduler;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.i18n.client.DateTimeFormat;
import com.google.gwt.i18n.client.DateTimeFormat.PredefinedFormat;
import com.google.gwt.i18n.client.NumberFormat;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.maps.client.MapWidget;
import com.google.gwt.maps.client.base.LatLng;
import com.google.gwt.maps.client.base.LatLngBounds;
import com.google.gwt.maps.client.events.mousedown.MouseDownMapHandler;
import com.google.gwt.maps.client.events.mouseout.MouseOutMapHandler;
import com.google.gwt.maps.client.events.mouseover.MouseOverMapHandler;
import com.google.gwt.maps.client.overlays.InfoWindow;
import com.google.gwt.maps.client.overlays.InfoWindowOptions;
import com.google.gwt.maps.client.overlays.Marker;
import com.google.gwt.maps.client.overlays.MarkerImage;
import com.google.gwt.maps.client.overlays.MarkerOptions;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.MenuItem;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.datepicker.client.DateBox;

class SensorInformation {
	private SpectrumBrowserShowDatasets spectrumBrowserShowDatasets;
	private JSONObject locationMessageJsonObject;
	private DateBox startDateCalendar;
	private MenuBar runLengthMenuBar;
	private Button showStatisticsButton;
	private Button showSensorDataButton;
	private Button showLastCaptureButton;
	private Button downloadDataButton;
	private MenuBar userDayCountMenuBar;
	private Label userDayCountLabel;
	private MenuBar selectFrequency;
	private MenuBar sensorSelectFrequency;
	private Label sensorSelectFrequencyLabel;
	private String measurementType = "FFT-Power";

	private long tStart;
	private long tStartLocalTime;
	private String tStartLocalTimeFormattedTimeStamp;

	private long tSelectedStartTime = -1;
	protected long tStartDayBoundary;
	private long dayBoundaryDelta = 0;

	private boolean selected;
	private long tStartReadings;
	private long tEndReadings;
	private long tEndReadingsLocalTime;
	private String tEndLocalTimeFormattedTimeStamp;

	private long tAquisitionStart;
	private long tAquisitionEnd;

	private float maxOccupancy;
	private float minOccupancy;
	private float meanOccupancy;
	private float dataSetMaxOccupancy;
	private float dataSetMinOccupancy;
	private float dataSetMeanOccupancy;
	private long readingsCount;
	private long acquistionCount;
	private boolean firstUpdate = true;
	private int dayCount = -1;
	private HashSet<FrequencyRange> frequencyRanges = new HashSet<FrequencyRange>();
	private long minFreq = -1;
	private long maxFreq = -1;
	private long subBandMinFreq;
	private long subBandMaxFreq;
	private String dataSetAcquistionStartLocalTime;
	private String dataSetAcquistionEndLocalTime;
	private boolean firstSummaryUpdate = true;
	private String tAcquisitionStartFormattedTimeStamp;
	private String tAcquisitionEndFormattedTimeStamp;

	private HTML info;
	private JSONObject systemMessageJsonObject;
	private String sys2detect;

	private Marker marker;
	private SpectrumBrowser spectrumBrowser;
	private InfoWindow infoWindow;
	private TextBox minFreqBox;
	private TextBox maxFreqBox;
	private VerticalPanel sensorInfoPanel;
	private MarkerOptions markerOptions;
	private LatLng displayPosition;
	private LatLng position;
	public FrequencyRange selectedFreqRange = null;
	private String baseUrl;
	private String sensorId;
	private int zIndex = 0;

	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	private float round(double val) {
		return (float) ((int) ((val + .05) * 10) / 10.0);
	}

	public LatLng getLatLng() {
		return position;
	}

	class SensorSelectFreqCommand implements Scheduler.ScheduledCommand {
		FrequencyRange freqRange;

		SensorSelectFreqCommand(FrequencyRange frequencyRange) {
			this.freqRange = frequencyRange;
		}

		@Override
		public void execute() {
			if (SensorInformation.this.selectedFreqRange == null
					|| !SensorInformation.this.selectedFreqRange
							.equals(freqRange)) {
				SensorInformation.this.selectedFreqRange = freqRange;
				SensorInformation.this.minFreq = freqRange.minFreq;
				SensorInformation.this.maxFreq = freqRange.maxFreq;
				SensorInformation.this.sys2detect = freqRange.sys2detect;
				sensorSelectFrequencyLabel.setText(freqRange.toString());
				updateDataSummary();
			}
		}

	}

	class SelectUserDayCountCommand implements Scheduler.ScheduledCommand {

		private int dc;

		public SelectUserDayCountCommand(int dayCount) {
			this.dc = dayCount;
		}

		@Override
		public void execute() {
			try {
				SensorInformation.this.setDayCount(dc);
				updateDataSummary();
			} catch (Exception ex) {
				logger.log(Level.SEVERE, "SelectUserDayCountCommand.execute:",
						ex);
			}
		}

	}

	public void setSelected(boolean flag) {
		selected = flag;
		logger.finer("SensorInformation: setSelected " + flag);
		if (!flag) {
			String iconPath = SpectrumBrowser.getIconsPath() + "mm_20_red.png";
			MarkerImage icon = MarkerImage.newInstance(iconPath);
			marker.setIcon(icon);
			this.spectrumBrowserShowDatasets.selectedMarker = null;
			this.spectrumBrowserShowDatasets.selectionGrid
					.remove(startDateCalendar);
			this.spectrumBrowserShowDatasets.selectionGrid
					.remove(sensorSelectFrequency);
			firstSummaryUpdate = true;
			this.spectrumBrowserShowDatasets.selectionGrid
					.remove(runLengthMenuBar);
			this.spectrumBrowserShowDatasets.selectionGrid
					.remove(userDayCountLabel);
			this.spectrumBrowserShowDatasets.selectionGrid
					.remove(sensorSelectFrequencyLabel);
			this.spectrumBrowserShowDatasets.selectionGrid
					.remove(showSensorDataButton);
			this.spectrumBrowserShowDatasets.selectionGrid
					.remove(downloadDataButton);
			this.spectrumBrowserShowDatasets.selectionGrid.setVisible(false);
		} else {
			String iconPath = SpectrumBrowser.getIconsPath()
					+ "mm_20_yellow.png";
			MarkerImage icon = MarkerImage.newInstance(iconPath);
			marker.setIcon(icon);
			this.spectrumBrowserShowDatasets.selectedMarker = this;
			this.spectrumBrowserShowDatasets.selectionGrid.setWidget(0, 0,
					startDateCalendar);
			this.spectrumBrowserShowDatasets.selectionGrid.setWidget(0, 1,
					runLengthMenuBar);
			this.spectrumBrowserShowDatasets.selectionGrid.setWidget(0, 2,
					userDayCountLabel);
			this.spectrumBrowserShowDatasets.selectionGrid.setWidget(0, 3,
					selectFrequency);
			this.spectrumBrowserShowDatasets.selectionGrid.setWidget(0, 4,
					sensorSelectFrequencyLabel);
			this.spectrumBrowserShowDatasets.selectionGrid.setWidget(0, 5,
					showStatisticsButton);
			if (measurementType.equals("FFT-Power")) {
				this.spectrumBrowserShowDatasets.selectionGrid.setWidget(0, 6,
						showSensorDataButton);
				this.spectrumBrowserShowDatasets.selectionGrid.setWidget(0, 7,
						showLastCaptureButton);
				this.spectrumBrowserShowDatasets.selectionGrid.setWidget(0, 8,
						downloadDataButton);
			} else {
				this.spectrumBrowserShowDatasets.selectionGrid.setWidget(0, 6,
						downloadDataButton);
			}
			this.spectrumBrowserShowDatasets.selectionGrid.setVisible(true);
		}

	}

	public HashSet<FrequencyRange> getFrequencyRanges() {
		return this.frequencyRanges;
	}

	public boolean isSelected() {
		return selected;
	}

	private long getSelectedDayBoundary(long time) {
		JsDate jsDate = JsDate.create(time * 1000);
		jsDate.setHours(0, 0, 0, 0);
		return (long) jsDate.getTime() / 1000;
	}

	private String getFormattedDate(long timeSeconds) {
		DateTimeFormat dateTimeFormat = DateTimeFormat
				.getFormat(PredefinedFormat.DATE_SHORT);
		return dateTimeFormat.format(new Date(timeSeconds * 1000));
	}

	private void updateDataSummary() {
		// Convert the selected start time to utc
		long startTime = getSelectedStartTime() + dayBoundaryDelta;
		logger.fine("UpdateDataSummary " + startTime + " dayCount "
				+ getDayCount());
		String sensorId = getId();
		double lat = this.locationMessageJsonObject.get("Lat").isNumber()
				.doubleValue();
		double lng = this.locationMessageJsonObject.get("Lon").isNumber()
				.doubleValue();
		double alt = this.locationMessageJsonObject.get("Alt").isNumber()
				.doubleValue();
		spectrumBrowser.getSpectrumBrowserService().getDataSummary(sensorId,
				lat, lng, alt, startTime, getDayCount(), minFreq, maxFreq,
				new SpectrumBrowserCallback<String>() {

					@Override
					public void onSuccess(String text) {
						try {
							logger.fine(text);
							JSONObject jsonObj = (JSONObject) JSONParser
									.parseLenient(text);
							String status = jsonObj.get("Status").isString().stringValue();
							if ( status.equals("NOK")) {
								return;
							}
							readingsCount = (long) jsonObj.get("readingsCount")
									.isNumber().doubleValue();
							if (readingsCount == 0) {
								return;
							}

							measurementType = jsonObj.get("measurementType")
									.isString().stringValue();
							logger.finer(measurementType);

							tStartReadings = (long) jsonObj
									.get("tStartReadings").isNumber()
									.doubleValue();
							logger.finer("tStartReadings " + tStartReadings);

							tAquisitionStart = (long) jsonObj
									.get("tAquistionStart").isNumber()
									.doubleValue();
							tAquisitionEnd = (long) jsonObj
									.get("tAquisitionEnd").isNumber()
									.doubleValue();
							tAcquisitionStartFormattedTimeStamp = jsonObj
									.get("tAquisitionStartFormattedTimeStamp")
									.isString().stringValue();
							tAcquisitionEndFormattedTimeStamp = jsonObj
									.get("tAquisitionEndFormattedTimeStamp")
									.isString().stringValue();
							tEndReadings = (long) jsonObj.get("tEndReadings")
									.isNumber().doubleValue();

							maxOccupancy = round(jsonObj.get("maxOccupancy")
									.isNumber().doubleValue());
							minOccupancy = round(jsonObj.get("minOccupancy")
									.isNumber().doubleValue());
							meanOccupancy = round(jsonObj.get("meanOccupancy")
									.isNumber().doubleValue());

							logger.finer("meanOccupancy" + meanOccupancy);
							tStartLocalTime = (long) jsonObj
									.get("tStartLocalTime").isNumber()
									.doubleValue();
							tStartDayBoundary = (long) jsonObj
									.get("tStartDayBoundary").isNumber()
									.doubleValue();
							setSelectedStartTime(tStartDayBoundary);
							dayBoundaryDelta = tStartDayBoundary
									- getSelectedDayBoundary((long) jsonObj
											.get("tStartDayBoundary")
											.isNumber().doubleValue());
							tStartLocalTimeFormattedTimeStamp = jsonObj
									.get("tStartLocalTimeFormattedTimeStamp")
									.isString().stringValue();
							logger.finer("tStartLocalTime " + tStartLocalTime);
							tEndReadingsLocalTime = (long) jsonObj
									.get("tEndReadingsLocalTime").isNumber()
									.doubleValue();
							tEndLocalTimeFormattedTimeStamp = jsonObj
									.get("tEndLocalTimeFormattedTimeStamp")
									.isString().stringValue();
							logger.finer("tEndReadings " + tEndReadings);

							dataSetMaxOccupancy = round(jsonObj
									.get("acquistionMaxOccupancy").isNumber()
									.doubleValue());
							dataSetMinOccupancy = round(jsonObj
									.get("acquistionMinOccupancy").isNumber()
									.doubleValue());
							dataSetMeanOccupancy = round(jsonObj
									.get("aquistionMeanOccupancy").isNumber()
									.doubleValue());
							dataSetAcquistionStartLocalTime = jsonObj
									.get("tAquisitionStartFormattedTimeStamp")
									.isString().stringValue();
							dataSetAcquistionEndLocalTime = jsonObj
									.get("tAquisitionEndFormattedTimeStamp")
									.isString().stringValue();
							acquistionCount = (long) jsonObj
									.get("acquistionCount").isNumber()
									.doubleValue();

							if (firstUpdate) {
								firstUpdate = false;
							} else {
								// Otherwise, immediately show the updates
								// of summary data.
								showSummary();
							}
						} catch (Throwable ex) {
							logger.log(Level.SEVERE,
									"Error Parsing returned data ", ex);
							SensorInformation.this.spectrumBrowserShowDatasets.spectrumBrowser
									.displayError("Error parsing returned data!");
						}
						// iwo.setPixelOffet(Size.newInstance(0, .1));

					}

					@Override
					public void onFailure(Throwable throwable) {
						logger.log(Level.SEVERE,
								"Error occured in processing request",
								throwable);
						SensorInformation.this.spectrumBrowserShowDatasets.spectrumBrowser
								.displayError("Error in contacting server. Try later");
						return;

					}

				});
	}

	public void showMarker() {
		try {
			MapWidget mapWidget = SpectrumBrowserShowDatasets.getMap();
			LatLngBounds bounds = mapWidget.getBounds();
			if (bounds.contains(position)) {
				LatLng northeast = bounds.getNorthEast();
				LatLng southwest = bounds.getSouthWest();
				double delta = Math.abs(northeast.getLatitude()
						- southwest.getLatitude());
				double deltaPerPixel = delta / mapWidget.getOffsetHeight();
				
				int desiredPixelOffset = zIndex * 10;
				logger.finer("Zindex = " + zIndex);
				double latOffset = desiredPixelOffset * deltaPerPixel;
				double lonOffset = desiredPixelOffset * deltaPerPixel;
				this.displayPosition = LatLng.newInstance(
						position.getLatitude() + latOffset,
						position.getLongitude() + lonOffset);

				marker.setPosition(displayPosition);
				marker.setVisible(true);
			} else {
				marker.setVisible(false);
			}
		} catch (Throwable ex) {
			logger.log(Level.SEVERE,
					"showMarker: Error creating sensor marker", ex);
			this.spectrumBrowserShowDatasets.spectrumBrowser
					.displayError("Internal error creating marker");
		}

	}

	public SensorInformation(
			SpectrumBrowserShowDatasets spectrumBrowserShowDatasets,
			double latitude, double longitude, MarkerOptions markerOptions,
			VerticalPanel sensorInfoPanel,
			JSONObject locationMessageJsonObject,
			JSONObject systemMessageObject, String baseUrl) {

		try {
			
			logger.finer("zIndex = " + this.zIndex);

			this.spectrumBrowserShowDatasets = spectrumBrowserShowDatasets;
			logger.finer("SensorInformation: baseUrl = " + baseUrl);
			this.baseUrl = baseUrl;
			this.sensorId = locationMessageJsonObject.get("SensorID")
					.isString().stringValue();
			SpectrumBrowser.addSensor(this);
			this.sensorInfoPanel = sensorInfoPanel;
			this.spectrumBrowser = spectrumBrowserShowDatasets.spectrumBrowser;
			this.marker = Marker.newInstance(markerOptions);
			this.markerOptions = markerOptions;
			this.position = LatLng.newInstance(latitude, longitude);
			marker.setMap(SpectrumBrowserShowDatasets.getMap());
			startDateCalendar = new DateBox();
			startDateCalendar.setTitle("Start Date");
			showStatisticsButton = new Button("Generate Daily Occupancy Chart");
			showStatisticsButton
					.setTitle("Click to see a chart of the daily occupancy");
			showStatisticsButton
					.setTitle("Click to generate daily occupancy chart");
			runLengthMenuBar = new MenuBar(true);
			userDayCountMenuBar = new MenuBar(true);
			userDayCountLabel = new Label();
			selectFrequency = new MenuBar(true);
			sensorSelectFrequency = new MenuBar(true);
			sensorSelectFrequencyLabel = new Label();
			selectFrequency.addItem("Freq Band", sensorSelectFrequency);
			userDayCountMenuBar = new MenuBar(true);
			runLengthMenuBar.addItem("Duration (days)", userDayCountMenuBar);
			
			for (SensorInformation sm : spectrumBrowserShowDatasets.getSensorMarkers()) {
				if (Math.abs(sm.getLatLng().getLatitude() - this.getLatLng().getLatitude()) < .1 &&
						Math.abs(sm.getLatLng().getLongitude() - this.getLatLng().getLongitude()) < .1) {
					this.zIndex ++;
				}
			}
			this.markerOptions.setZindex(zIndex);

			showStatisticsButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(
						com.google.gwt.event.dom.client.ClickEvent event) {
					if (isSelected()) {
						long startTime = getSelectedStartTime()
								+ dayBoundaryDelta;
						int days = getDayCount();
						logger.finer("Day Count = " + days + " startTime = "
								+ startTime);
						if (days > 0) {
							SensorInformation.this.spectrumBrowserShowDatasets
									.setStatus("Computing Occupancy Chart -- please wait");
							ArrayList<SpectrumBrowserScreen> navigation = new ArrayList<SpectrumBrowserScreen>();
							navigation
									.add(SensorInformation.this.spectrumBrowserShowDatasets);

							new DailyStatsChart(
									SensorInformation.this.spectrumBrowserShowDatasets.spectrumBrowser,
									navigation,
									getId(),
									startTime,
									days,
									getSys2Detect(),
									getMinFreq(),
									getMaxFreq(),
									getSubBandMinFreq(),
									getSubBandMaxFreq(),
									measurementType,
									SensorInformation.this.spectrumBrowserShowDatasets.verticalPanel,
									SpectrumBrowser.MAP_WIDTH,
									SpectrumBrowser.MAP_HEIGHT / 2);
						}
					}
				}

			});

			showSensorDataButton = new Button("Live Sensor Data");
			showSensorDataButton
					.setTitle("Click to see near real-time sensor readings");

			showSensorDataButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					new SensorDataStream(
							getId(),
							SensorInformation.this.spectrumBrowserShowDatasets.verticalPanel,
							SensorInformation.this.spectrumBrowserShowDatasets.spectrumBrowser,
							SensorInformation.this.spectrumBrowserShowDatasets)
							.draw();
				}
			});

			showLastCaptureButton = new Button("Last Capture");

			showLastCaptureButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					SensorInformation.this.spectrumBrowserShowDatasets.spectrumBrowser
							.getSpectrumBrowserService()
							.getLastAcquisitionTime(getId(), sys2detect,
									minFreq, maxFreq,
									new SpectrumBrowserCallback<String>() {

										@Override
										public void onSuccess(String result) {
											JSONValue jsonValue = JSONParser
													.parseLenient(result);
											long selectionTime = (long) jsonValue
													.isObject()
													.get("aquisitionTimeStamp")
													.isNumber().doubleValue();
											if (selectionTime != -1) {
												ArrayList<SpectrumBrowserScreen> navigation = new ArrayList<SpectrumBrowserScreen>();
												navigation
														.add(SensorInformation.this.spectrumBrowserShowDatasets);
												new FftPowerOneAcquisitionSpectrogramChart(
														getId(),
														selectionTime,
														sys2detect,
														minFreq,
														maxFreq,
														SensorInformation.this.spectrumBrowserShowDatasets.verticalPanel,
														spectrumBrowser,
														navigation,
														SpectrumBrowser.MAP_WIDTH,
														SpectrumBrowser.MAP_HEIGHT);
											} else {
												Window.alert("No capture found");
											}
										}

										@Override
										public void onFailure(
												Throwable throwable) {
											logger.log(
													Level.SEVERE,
													"Problem communicating with web server",
													throwable);
										}
									});

				}

			});

			downloadDataButton = new Button("Download Data");

			downloadDataButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					ArrayList<SpectrumBrowserScreen> navigation = new ArrayList<SpectrumBrowserScreen>();
					navigation
							.add(SensorInformation.this.spectrumBrowserShowDatasets);
					new DowloadData(
							getId(),
							tSelectedStartTime,
							dayCount,
							sys2detect,
							minFreq,
							maxFreq,
							SensorInformation.this.spectrumBrowserShowDatasets.verticalPanel,
							SensorInformation.this.spectrumBrowserShowDatasets.spectrumBrowser,
							navigation).draw();

				}

			});

			this.locationMessageJsonObject = locationMessageJsonObject;
			this.systemMessageJsonObject = systemMessageObject;
			// Extract the data values.
			tStart = (long) locationMessageJsonObject.get("t").isNumber()
					.doubleValue();
			tStartLocalTime = (long) locationMessageJsonObject
					.get("tStartLocalTime").isNumber().doubleValue();
			updateDataSummary();

			startDateCalendar
					.addValueChangeHandler(new ValueChangeHandler<Date>() {

						@Override
						public void onValueChange(ValueChangeEvent<Date> event) {
							logger.finer("Calendar valueChanged "
									+ event.getValue().getTime()
									+ " tStartLocalTime " + tStartLocalTime
									* 1000 + " tEndLocalTime "
									+ tEndReadingsLocalTime * 1000);
							Date eventDate = event.getValue();
							if (eventDate.getTime() <= getSelectedDayBoundary(tAquisitionStart) * 1000) {
								setSelectedStartTime(getSelectedDayBoundary(tAquisitionStart));
								updateDataSummary();
							} else if (eventDate.getTime() >= tAquisitionEnd * 1000) {
								setSelectedStartTime(getSelectedDayBoundary(tAquisitionStart));
								updateDataSummary();

							} else {
								logger.finer("Date in acceptable range");
								setSelectedStartTime(getSelectedDayBoundary(eventDate
										.getTime() / 1000));
								updateDataSummary();
							}

						}
					});

		} catch (Exception ex) {
			logger.log(Level.SEVERE, "Error creating sensor marker", ex);
			this.spectrumBrowserShowDatasets.spectrumBrowser
					.displayError("Internal error creating marker");
		}
	}

	public String getBaseUrl() {
		return this.baseUrl;
	}

	public double getAlt() {
		return locationMessageJsonObject.get("Alt").isNumber().doubleValue();
	}

	public String getCotsSensorModel() {
		return systemMessageJsonObject.get("COTSsensor").isObject()
				.get("Model").isString().stringValue();
	}

	public String getSensorAntennaType() {
		return systemMessageJsonObject.get("Antenna").isObject().get("Model")
				.isString().stringValue();

	}

	public String getInfo() {

		return "<b color=\"red\" > Click on marker to select sensor. </b>"
				+ "<div align=\"left\", height=\"300px\">"
				+ "<br/>sensor ID = "
				+ getId()
				+ "<br/>Lat = "
				+ NumberFormat.getFormat("00.00").format(
						getLatLng().getLatitude())
				+ " Long = "
				+ NumberFormat.getFormat("00.00").format(
						getLatLng().getLongitude())
				+ " Alt = "
				+ this.formatToPrecision(2, getAlt())
				+ " Ft."
				+ "<br/> Sensor ID = "
				+ this.getId()
				+ "<br/> Sensor Model = "
				+ getCotsSensorModel()
				+ "; Antenna Type = "
				+ getSensorAntennaType()
				+ "; Measurement Type = "
				+ measurementType
				+ "<br/> Start = "
				+ dataSetAcquistionStartLocalTime
				+ " End = "
				+ dataSetAcquistionEndLocalTime
				+ "<br/>freqRanges = "
				+ getFormattedFrequencyRanges()
				+ "Max Occupancy = "
				+ this.formatToPrecision(2, dataSetMaxOccupancy * 100)
				+ "%"
				+ " Min Occupancy = "
				+ this.formatToPrecision(2, dataSetMinOccupancy * 100)
				+ "%"
				+ "; Mean Occupancy = "
				+ this.formatToPrecision(2, dataSetMeanOccupancy * 100)
				+ "%"
				+ "<br/>Aquisition Count = "
				+ acquistionCount
				+ "<br/><br/></div>";
	}

	private String getFormattedFrequencyRanges() {
		StringBuilder retval = new StringBuilder();
		for (FrequencyRange r : this.frequencyRanges) {
			retval.append(r.toString() + " <br/>");
		}
		return retval.toString();
	}

	public String getTstartLocalTimeAsString() {
		return dataSetAcquistionStartLocalTime;
	}

	public String getTendReadingsLocalTimeAsString() {
		return dataSetAcquistionEndLocalTime;
	}

	public String getId() {
		return sensorId;
	}

	double getMaxOccupancy() {
		return maxOccupancy;
	}

	double getMinOccupancy() {
		return minOccupancy;
	}

	double getMeanOccupancy() {
		return meanOccupancy;
	}

	String getSys2Detect() {
		return this.sys2detect;
	}

	long getMinFreq() {
		return minFreq;
	}

	long getMaxFreq() {
		return maxFreq;
	}

	long getSubBandMinFreq() {
		return subBandMinFreq;
	}

	long getSubBandMaxFreq() {
		return subBandMaxFreq;
	}

	long getReadingsCount() {
		return readingsCount;
	}

	public String formatToPrecision(int precision, double value) {
		String format = "00.";
		for (int i = 0; i < precision; i++) {
			format += "0";
		}
		return NumberFormat.getFormat(format).format(value);
	}

	void setSensorInfoPanel(VerticalPanel sensorInfoPanel) {
		this.sensorInfoPanel = sensorInfoPanel;
	}

	void setFirstUpdate(boolean firstUpdate) {
		this.firstUpdate = firstUpdate;
		this.firstSummaryUpdate = firstUpdate;
	}

	void showSummary() {
		logger.finer("showSummary");
		try {
			if (firstSummaryUpdate) {
				firstSummaryUpdate = false;
				sensorSelectFrequency.clearItems();
				boolean firstItem = true;
				for (FrequencyRange r : frequencyRanges) {
					MenuItem menuItem = new MenuItem(new SafeHtmlBuilder()
							.appendEscaped(r.toString()).toSafeHtml(),
							new SensorSelectFreqCommand(r));
					if (firstItem) {
						this.selectedFreqRange = r;
						this.minFreq = r.minFreq;
						this.maxFreq = r.maxFreq;
						this.sys2detect = r.sys2detect;
					}
					firstItem = false;
					sensorSelectFrequencyLabel.setText(new FrequencyRange(
							sys2detect, minFreq, maxFreq).toString());
					sensorSelectFrequency.addItem(menuItem);

				}
				updateDataSummary();
			}

			String sid = getId();
			String minOccupancyVal = this.formatToPrecision(2,
					minOccupancy * 100) + "%";
			String maxOccupancyVal = this.formatToPrecision(2,
					maxOccupancy * 100) + "%";
			String meanOccupancyVal = this.formatToPrecision(2,
					meanOccupancy * 100) + "%";

			int rcount = (int) readingsCount;

			sensorInfoPanel.clear();
			startDateCalendar.setEnabled(true);
			final int maxDayCount = (int) ((double) (tAquisitionEnd - getSelectedStartTime())
					/ (double) SpectrumBrowserShowDatasets.SECONDS_PER_DAY + .5);
			logger.finer("maxDayCount " + maxDayCount);
			final int allowableDayCount = measurementType.equals("FFT-Power") ? Math
					.min(14, maxDayCount) : Math.min(30, maxDayCount);
			userDayCountMenuBar.clearItems();
			for (int i = 0; i < allowableDayCount; i++) {
				MenuItem menuItem = new MenuItem(Integer.toString(i + 1),
						new SelectUserDayCountCommand(i + 1));
				userDayCountMenuBar.addItem(menuItem);
			}
			if (dayCount == -1 || dayCount > allowableDayCount) {
				logger.finer("allowableDayCount : " + allowableDayCount);
				setDayCount(allowableDayCount);
			}

			info = new HTML(
					"<h3>Sensor Information</h3>" + "<b>Sensor ID: "
							+ sid
							+ "<br/>Sensor Model:  "
							+ getCotsSensorModel()
							+ "<br/>Antenna Type: "
							+ getSensorAntennaType()
							+ "<br/>Measurement Type: "
							+ measurementType
							+ "<br/>Available Data Start: "
							+ tAcquisitionStartFormattedTimeStamp
							+ "<br/>Available Data End:"
							+ tAcquisitionEndFormattedTimeStamp
							+ "<br/>Available acquisition count: "
							+ acquistionCount
							+ "<br/>Frequency Band: "
							+ new FrequencyRange(sys2detect, minFreq, maxFreq)
									.toString()
							+ "<br/>Selected start date: "
							+ getFormattedDate(getSelectedDayBoundary(getSelectedStartTime()))
							+ "<br/>Duration: " + getDayCount() + " days"
							+ "<br/>Acquistion count: " + rcount
							+ "<br/>Min occupancy: " + minOccupancyVal
							+ "<br/>Max occupancy: " + maxOccupancyVal
							+ "<br/>Mean occupancy: " + meanOccupancyVal
							+ "</b>");
			// info.setStyleName("sensorInfo");
			sensorInfoPanel.add(info);
			subBandMinFreq = this.minFreq;
			subBandMaxFreq = this.maxFreq;

			if (measurementType.equals("Swept-frequency")) {
				sensorInfoPanel.add(new HTML("<h4>Specify Sub-band: </h4>"));
				HorizontalPanel hp = new HorizontalPanel();
				sensorInfoPanel.add(hp);
				hp.add(new Label("Min Freq (MHz):"));
				minFreqBox = new TextBox();
				minFreqBox.setText(Double.toString(minFreq / 1E6));
				minFreqBox
						.addValueChangeHandler(new ValueChangeHandler<String>() {
							@Override
							public void onValueChange(
									ValueChangeEvent<String> event) {
								try {
									double newFreq = Double.parseDouble(event
											.getValue());
									if (newFreq * 1E6 > maxFreq) {
										Window.alert("Value too large.");
										maxFreqBox.setText(Double
												.toString(maxFreq / 1E6));
										return;
									}
									if (newFreq * 1E6 < minFreq) {
										Window.alert("Value too small.");
										minFreqBox.setText(Double
												.toString(minFreq / 1E6));
										return;
									}
									subBandMinFreq = (long) (newFreq * 1E6);
								} catch (NumberFormatException ex) {
									Window.alert("Illegal Entry");
									maxFreqBox.setText(Double.toString(maxFreq));
								}

							}
						});
				hp.add(minFreqBox);
				hp = new HorizontalPanel();
				sensorInfoPanel.add(hp);
				hp.add(new Label("Max Freq (MHz):"));
				maxFreqBox = new TextBox();
				maxFreqBox
						.addValueChangeHandler(new ValueChangeHandler<String>() {
							@Override
							public void onValueChange(
									ValueChangeEvent<String> event) {
								try {
									double newFreq = Double.parseDouble(event
											.getValue());
									if (newFreq * 1E6 > maxFreq) {
										Window.alert("Value too large.");
										maxFreqBox.setText(Double
												.toString(maxFreq / 1E6));
										return;
									}
									if (newFreq * 1E6 < minFreq) {
										Window.alert("Value too small.");
										minFreqBox.setText(Double
												.toString(minFreq / 1E6));
										return;
									}
									subBandMaxFreq = (long) (newFreq * 1E6);

								} catch (NumberFormatException ex) {
									Window.alert("Illegal Entry");
									maxFreqBox.setText(Double.toString(maxFreq));
								}

							}
						});
				maxFreqBox.setText(Double.toString(maxFreq / 1E6));
				hp.add(maxFreqBox);
				sensorInfoPanel.add(hp);
			}
			sensorInfoPanel.setBorderWidth(2);

			if (rcount > 0) {
				showStatisticsButton.setEnabled(true);
			} else {
				Window.alert("No aquisitions found in selected interval. Please choose another.");
			}
		} catch (Exception ex) {
			logger.log(Level.SEVERE, "Error in updating data summary ", ex);
		}

	}

	public long getSelectedStartTime() {
		return this.tSelectedStartTime;
	}

	void setDayCount(int dayCount) throws Exception {
		logger.finer("setDayCount: " + dayCount);
		if (dayCount <= 0) {
			throw new Exception("Bad day count setting.");
		}
		this.dayCount = dayCount;
		userDayCountLabel.setText(Integer.toString(dayCount));
	}

	public int getDayCount() {
		return this.dayCount;
	}

	public InfoWindow getInfoWindow() {
		LatLng northeast = SpectrumBrowserShowDatasets.getMap().getBounds()
				.getNorthEast();
		LatLng southwest = SpectrumBrowserShowDatasets.getMap().getBounds()
				.getSouthWest();
		double delta = northeast.getLatitude() - southwest.getLatitude();
		int height = SpectrumBrowser.MAP_HEIGHT;
		// should be the height of the icon.
		int desiredPixelOffset = 15;
		double latitudeOffset = delta / height * desiredPixelOffset;
		InfoWindowOptions iwo = InfoWindowOptions.newInstance();

		iwo.setPosition(LatLng.newInstance(getLatLng().getLatitude()
				+ latitudeOffset, getLatLng().getLongitude()));
		iwo.setDisableAutoPan(true);
		iwo.setContent(getInfo());
		this.infoWindow = InfoWindow.newInstance(iwo);
		return infoWindow;
	}

	public void closeInfoWindow() {
		infoWindow.close();
	}

	public void setFrequencyRanges(HashSet<FrequencyRange> freqRanges) {
		FrequencyRange selectedFreqRange = freqRanges.iterator().next();
		this.minFreq = selectedFreqRange.minFreq;
		this.maxFreq = selectedFreqRange.maxFreq;
		this.frequencyRanges.addAll(freqRanges);
	}

	void setSelectedStartTime(long tSelectedStartTime) {
		logger.finer("setSelectedStartTime: " + tSelectedStartTime);
		this.tSelectedStartTime = tSelectedStartTime;
		startDateCalendar.setValue(new Date(
				getSelectedDayBoundary(tSelectedStartTime) * 1000));
		startDateCalendar.getDatePicker().setValue(
				new Date(getSelectedDayBoundary(tSelectedStartTime)));
		startDateCalendar.getDatePicker().setCurrentMonth(
				new Date(getSelectedDayBoundary(tSelectedStartTime)));

	}

	public void addMouseOverHandler(MouseOverMapHandler mouseOverMapHandler) {
		this.marker.addMouseOverHandler(mouseOverMapHandler);
	}

	public void addMouseOutMoveHandler(MouseOutMapHandler mouseOutMapHandler) {
		this.marker.addMouseOutMoveHandler(mouseOutMapHandler);
	}

	public void addMouseDownHandler(MouseDownMapHandler mouseDownMapHandler) {
		this.marker.addMouseDownHandler(mouseDownMapHandler);

	}

	public void setVisible(boolean b) {
		this.marker.setVisible(b);
	}

	public void setMap(MapWidget map) {
		marker.setMap(map);
	}

	public boolean containsSys2Detect(String sys2Detect) {
		for (FrequencyRange range : this.frequencyRanges) {
			if (range.sys2detect.equals(sys2Detect)) {
				return true;
			}
		}
		return false;
	}

	public int getMarkerZindex() {
		return zIndex;
	}

}