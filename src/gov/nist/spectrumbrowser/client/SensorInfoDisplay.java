package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.Defines;
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
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.MenuItem;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.datepicker.client.DateBox;

class SensorInfoDisplay {
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
	private Label readingsCountLabel;

	private long tSelectedStartTime = -1;
	protected long tStartDayBoundary;
	private long dayBoundaryDelta = 0;

	private boolean selected;

	private int dayCount = -1;

	private long minFreq = -1;
	private long maxFreq = -1;

	private HTML info;
	private SpectrumBrowser spectrumBrowser;
	private TextBox minFreqBox;
	private TextBox maxFreqBox;
	private VerticalPanel sensorInfoPanel;
	private LatLng position;
	private String baseUrl;
	private SensorInfo sensorInfo;
	private VerticalPanel verticalPanel;
	private Grid selectionGrid;
	private HashSet<Button> selectionButtons;
	private VerticalPanel sensorDescriptionPanel;
	private BandInfo selectedBand;
	private Button showSensorInfoButton;

	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	private float round(double val) {
		return (float) ((int) ((val + .05) * 10) / 10.0);
	}

	public LatLng getLatLng() {
		return position;
	}

	class SelectUserDayCountCommand implements Scheduler.ScheduledCommand {

		private int dc;

		public SelectUserDayCountCommand(int dayCount) {
			this.dc = dayCount;
		}

		@Override
		public void execute() {
			try {
				SensorInfoDisplay.this.setDayCount(dc);
				updateAcquistionCount();
			} catch (Exception ex) {
				logger.log(Level.SEVERE, "SelectUserDayCountCommand.execute:",
						ex);
			}
		}

	}

	public void setSelected(boolean flag) {
		selected = flag;
		logger.finer("SensorInformation: setSelected " + flag + " sensorId = "
				+ getId());
		if (!flag) {
			selectionGrid.remove(startDateCalendar);
			selectionGrid.remove(runLengthMenuBar);
			selectionGrid.remove(userDayCountLabel);
			selectionGrid.remove(showSensorDataButton);
			selectionGrid.remove(downloadDataButton);
			selectionGrid.remove(showLastCaptureButton);
			selectionGrid.remove(readingsCountLabel);
			selectionGrid.setVisible(false);
			hideSummary();
			for (Button button : selectionButtons) {
				button.setStyleName("none");
			}

		} else {
			selectionGrid.setWidget(0, 0, startDateCalendar);
			selectionGrid.setWidget(0, 1, runLengthMenuBar);
			selectionGrid.setWidget(0, 2, userDayCountLabel);
			selectionGrid.setWidget(0, 3, readingsCountLabel);
			selectionGrid.setWidget(0, 4, showStatisticsButton);
			if (sensorInfo.getMeasurementType().equals("FFT-Power")) {
				selectionGrid.setWidget(0, 5, showSensorDataButton);
				selectionGrid.setWidget(0, 6, showLastCaptureButton);
				selectionGrid.setWidget(0, 7, downloadDataButton);
			} else {
				selectionGrid.setWidget(0, 5, downloadDataButton);
			}
			selectionGrid.setVisible(true);
			SpectrumBrowserShowDatasets.setSelectedSensor(getId());
 		}

	}

	public boolean isSelected() {
		return selected;
	}

	long getSelectedDayBoundary(long time) {
		JsDate jsDate = JsDate.create(time * 1000);
		jsDate.setHours(0, 0, 0, 0);
		return (long) jsDate.getTime() / 1000;
	}

	private void updateAcquistionCount() {
		// Convert the selected start time to utc
		long startTime = getSelectedStartTime() + dayBoundaryDelta;
		logger.fine("updateAcquistionCount " + startTime + " dayCount "
				+ getDayCount());

		this.selectedBand.updateAcquistionCount(startTime, dayCount,
				readingsCountLabel);

	}

	public SensorInfoDisplay(final SpectrumBrowser spectrumBrowser,
			final SpectrumBrowserShowDatasets spectrumBrowserShowDatasets,
			double latitude, double longitude, VerticalPanel vpanel,
			VerticalPanel sensorInfoPanel, Grid selectionGrid,
			JSONObject locationMessageJsonObject,
			JSONObject systemMessageObject, String baseUrl) throws Exception {

		try {
			this.spectrumBrowserShowDatasets = spectrumBrowserShowDatasets;
			logger.finer("SensorInformation: baseUrl = " + baseUrl);
			this.baseUrl = baseUrl;
			sensorInfo = new SensorInfo(systemMessageObject,
					locationMessageJsonObject, spectrumBrowser, this);
			SpectrumBrowser.addSensor(this);
			this.selectionGrid = selectionGrid;
			this.sensorInfoPanel = sensorInfoPanel;
			this.verticalPanel = vpanel;
			this.spectrumBrowser = spectrumBrowser;
			this.position = LatLng.newInstance(latitude, longitude);
			this.selectionButtons = new HashSet<Button>();
			initUiElements();
			sensorInfo.updateDataSummary(-1, dayCount, minFreq, maxFreq);
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Problem creating SensorInfoDisplay", th);
		}
	}

	void initUiElements() {
		try {
			sensorDescriptionPanel = new VerticalPanel();
			sensorDescriptionPanel.setVisible(false);
			sensorDescriptionPanel.setBorderWidth(2);
			sensorDescriptionPanel.setStyleName("sensorInformation");

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

			readingsCountLabel = new Label();
			readingsCountLabel.setText("measurements");

			userDayCountMenuBar = new MenuBar(true);
			runLengthMenuBar.addItem("Duration (days)", userDayCountMenuBar);

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
							SensorInfoDisplay.this.spectrumBrowserShowDatasets
									.setStatus("Computing Occupancy Chart -- please wait");
							ArrayList<SpectrumBrowserScreen> navigation = new ArrayList<SpectrumBrowserScreen>();
							navigation
									.add(SensorInfoDisplay.this.spectrumBrowserShowDatasets);

							new DailyStatsChart(
									SensorInfoDisplay.this.spectrumBrowser,
									navigation, getId(), startTime, days,
									sensorInfo.getSelectedBand()
											.getSysToDetect(), getMinFreq(),
									getMaxFreq(), getSubBandMinFreq(),
									getSubBandMaxFreq(), sensorInfo
											.getMeasurementType(),
									verticalPanel, SpectrumBrowser.MAP_WIDTH,
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
					new SensorDataStream(getId(), verticalPanel,
							spectrumBrowser, spectrumBrowserShowDatasets)
							.draw();
				}
			});

			showLastCaptureButton = new Button("Last Capture");

			showLastCaptureButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					SensorInfoDisplay.this.spectrumBrowser
							.getSpectrumBrowserService()
							.getLastAcquisitionTime(getId(), selectedBand.getSystemToDetect(),
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
											if (selectionTime != -1
													&& sensorInfo
															.getMeasurementType()
															.equals(Defines.FFT_POWER)) {
												ArrayList<SpectrumBrowserScreen> navigation = new ArrayList<SpectrumBrowserScreen>();
												navigation
														.add(SensorInfoDisplay.this.spectrumBrowserShowDatasets);
												new FftPowerOneAcquisitionSpectrogramChart(
														getId(),
														selectionTime,
														selectedBand.getSystemToDetect(),
														minFreq,
														maxFreq,
														verticalPanel,
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
							.add(SensorInfoDisplay.this.spectrumBrowserShowDatasets);
					new DowloadData(
							getId(),
							tSelectedStartTime,
							dayCount,
							selectedBand.getSystemToDetect(),
							minFreq,
							maxFreq,
							SensorInfoDisplay.this.spectrumBrowserShowDatasets.verticalPanel,
							SensorInfoDisplay.this.spectrumBrowser, navigation)
							.draw();

				}

			});

			startDateCalendar
					.addValueChangeHandler(new ValueChangeHandler<Date>() {

						@Override
						public void onValueChange(ValueChangeEvent<Date> event) {
							logger.finer("Calendar valueChanged "
									+ event.getValue().getTime());
							Date eventDate = event.getValue();
							if (eventDate.getTime() <= getSelectedDayBoundary(sensorInfo
									.gettStartReadings()) * 1000) {
								setSelectedStartTime(getSelectedDayBoundary(sensorInfo
										.gettStartReadings()));
								updateAcquistionCount();
							} else if (eventDate.getTime() >= sensorInfo
									.gettStartReadings() * 1000) {
								setSelectedStartTime(getSelectedDayBoundary(sensorInfo
										.gettEndReadings()));
								updateAcquistionCount();

							} else {
								logger.finer("Date in acceptable range");
								setSelectedStartTime(getSelectedDayBoundary(eventDate
										.getTime() / 1000));
								updateAcquistionCount();
							}

						}
					});
			showSensorInfoButton = new Button("Sensor: " + getId());
			showSensorInfoButton.setStyleName("dangerous");
			showSensorInfoButton.setTitle("Click to show/hide detail");
			showSensorInfoButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					if (sensorDescriptionPanel.isVisible()) {
						sensorDescriptionPanel.setVisible(false);
					} else
						sensorDescriptionPanel.setVisible(true);
				}

			});

		} catch (Exception ex) {
			logger.log(Level.SEVERE, "Error creating sensor marker", ex);
			spectrumBrowser.displayError("Internal error creating marker");
		}
	}

	public String getBaseUrl() {
		return this.baseUrl;
	}

	public double getAlt() {
		return locationMessageJsonObject.get("Alt").isNumber().doubleValue();
	}

	public String getId() {
		return this.sensorInfo.getSensorId();
	}

	long getMinFreq() {
		return minFreq;
	}

	long getMaxFreq() {
		return maxFreq;
	}

	long getSubBandMinFreq() {
		return sensorInfo.getSelectedBand().getMinFreq();
	}

	long getSubBandMaxFreq() {
		return sensorInfo.getSelectedBand().getMaxFreq();
	}

	/**
	 * Show the sensor summary information in the side of the map.
	 * 
	 */

	void buildSummary() {
		logger.finer("SensorInfoDisplay: buildSummary " + getId());

		try {

			info = sensorInfo.getSensorDescription();
			sensorDescriptionPanel.add(info);
			for (final String bandName : sensorInfo.getBandNames()) {
				final BandInfo bandInfo = sensorInfo.getBandInfo(bandName);
				if (bandInfo != null && bandInfo.getCount() != 0) {
					HTML bandDescription = sensorInfo
							.getBandDescription(bandName);

					sensorDescriptionPanel.add(bandDescription);

					if (sensorInfo.getMeasurementType().equals(
							"Swept-frequency")) {
						sensorDescriptionPanel.add(new Label(
								"Specify Sub-band :"));
						Grid grid = new Grid(2, 2);

						grid.setText(0, 0, "Min Freq (MHz):");
						minFreqBox = new TextBox();
						minFreqBox.setText(Double.toString(bandInfo
								.getSelectedMinFreq() / 1E6));
						minFreqBox
								.addValueChangeHandler(new ValueChangeHandler<String>() {
									@Override
									public void onValueChange(
											ValueChangeEvent<String> event) {
										try {
											double newFreq = Double
													.parseDouble(event
															.getValue());
											if (bandInfo
													.setSelectedMinFreq((long) (newFreq * 1E6))) {
												Window.alert("Illegal value entered");
												maxFreqBox.setText(Double.toString(bandInfo
														.getSelectedMinFreq()));
											}
										} catch (NumberFormatException ex) {
											Window.alert("Illegal Entry");
											minFreqBox.setText(Double.toString(bandInfo
													.getMinFreq() / 1E6));
										}

									}
								});
						grid.setWidget(0, 1, minFreqBox);

						grid.setText(1, 0, "Max Freq (MHz):");
						maxFreqBox = new TextBox();
						maxFreqBox
								.addValueChangeHandler(new ValueChangeHandler<String>() {
									@Override
									public void onValueChange(
											ValueChangeEvent<String> event) {
										try {
											double newFreq = Double
													.parseDouble(event
															.getValue());

											if (!bandInfo
													.setSelectedMaxFreq((long) (newFreq * 1E6))) {

												Window.alert("Illegal value entered");
												maxFreqBox.setText(Double.toString(bandInfo
														.getSelectedMaxFreq()));
											}
										} catch (NumberFormatException ex) {
											Window.alert("Illegal Entry");
											maxFreqBox.setText(Double.toString(bandInfo
													.getSelectedMaxFreq()));
										}

									}
								});
						maxFreqBox.setText(Double.toString(bandInfo
								.getSelectedMaxFreq() / 1E6));
						grid.setWidget(1, 1, maxFreqBox);
						sensorDescriptionPanel.add(grid);

					}
					final Button bandSelectionButton = new Button("Select");
					sensorDescriptionPanel.add(bandSelectionButton);
					selectionButtons.add(bandSelectionButton);

					bandSelectionButton.addClickHandler(new ClickHandler() {
						@Override
						public void onClick(ClickEvent event) {
							setSelected(true);
							for (Button button : selectionButtons) {
								button.setStyleName("none");
							}
							bandSelectionButton.setStyleName("sendButton");
							selectedBand = bandInfo;
							minFreq = bandInfo.getMinFreq();
							maxFreq = bandInfo.getMaxFreq();
							logger.finer("minFreq " + minFreq + " maxFreq "
									+ maxFreq);
							startDateCalendar.setEnabled(true);
							logger.finer("tEndReadings: "
									+ sensorInfo.gettEndReadings()
									+ " getSelectedStartTime : "
									+ getSelectedStartTime());
							final int maxDayCount = (int) ((double) (bandInfo
									.getTEndReadings() - getSelectedStartTime())
									/ (double) SpectrumBrowserShowDatasets.SECONDS_PER_DAY + .5);
							logger.finer("maxDayCount " + maxDayCount);
							final int allowableDayCount = sensorInfo
									.getMeasurementType().equals("FFT-Power") ? Math
									.min(14, maxDayCount) : Math.min(30,
									maxDayCount);
							userDayCountMenuBar.clearItems();
							for (int i = 0; i < allowableDayCount; i++) {
								MenuItem menuItem = new MenuItem(Integer
										.toString(i + 1),
										new SelectUserDayCountCommand(i + 1));
								userDayCountMenuBar.addItem(menuItem);
							}
							if (dayCount == -1 || dayCount > allowableDayCount) {
								logger.finer("allowableDayCount : "
										+ allowableDayCount);
								setDayCount(allowableDayCount);
							}
							updateAcquistionCount();
						}
					});
				}
			}

		} catch (Exception ex) {
			logger.log(Level.SEVERE, "Error in updating data summary ", ex);
			ex.printStackTrace();
		} finally {
		}

	}

	public long getSelectedStartTime() {
		return this.tSelectedStartTime;
	}

	void setDayCount(int dayCount) {
		logger.finer("setDayCount: " + dayCount);
		if (dayCount <= 0) {
			logger.log(Level.SEVERE, "Bad day count setting." + dayCount);
			return;
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
		iwo.setContent(sensorInfo.getSensorDescription());
		return InfoWindow.newInstance(iwo);
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

	public boolean containsSys2Detect(String sys2Detect) {
		return sensorInfo.containsSys2detect(sys2Detect);
	}

	public void setDayBoundaryDelta(long delta) {
		dayBoundaryDelta = delta;
	}

	public HashSet<FrequencyRange> getFreqRanges() {
		return sensorInfo.getFreqRanges();
	}

	public void showSummary(boolean minimize) {
		if (minimize) {
			if (showSensorInfoButton.getParent() == null ) {
				sensorInfoPanel.add(showSensorInfoButton);
			}
			if ( sensorDescriptionPanel.getParent() == null ) {
				sensorInfoPanel.add(sensorDescriptionPanel);
			}
		} else {
			if (sensorDescriptionPanel.getParent() == null ){
				sensorInfoPanel.add(sensorDescriptionPanel);
			}
			sensorDescriptionPanel.setVisible(true);
		}
		logger.finer("SensorInfoDisplay: showSummary : " + this.getId());
	}

	public void hideSummary() {
		
		sensorDescriptionPanel.setVisible(false);
		logger.finer("SensorInfoDisplay: showSummary : " + this.getId());

	}

}