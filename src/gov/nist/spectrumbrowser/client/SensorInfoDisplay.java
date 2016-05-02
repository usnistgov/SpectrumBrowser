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
import com.google.gwt.dom.client.Style.Cursor;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.maps.client.base.LatLng;
import com.google.gwt.maps.client.overlays.InfoWindow;
import com.google.gwt.maps.client.overlays.InfoWindowOptions;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
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
	private Button viewCaptureEventsButton;
	private MenuBar userDayCountMenuBar;
	private Label userDayCountLabel;
	private Label readingsCountLabel;

	private long tSelectedStartTime = -1;
	private long dayBoundaryDelta = 0;

	private boolean selected;

	public int dayCount = -1;
	
	private TextInputBox dayInputSelect;
	private SensorInfoDisplay sid;

	private HTML info;
	private SpectrumBrowser spectrumBrowser;
	private TextBox minFreqBox;
	private TextBox maxFreqBox;
	private VerticalPanel sensorInfoPanel;
	private LatLng position;
	private String baseUrl;
	public SensorInfo sensorInfo;
	private VerticalPanel verticalPanel;
	private Grid selectionGrid;
	private HashSet<Label> selectionButtons;
	private HashSet<VerticalPanel> bandDescriptionPanels;
	private VerticalPanel sensorDescriptionPanel;
	private BandInfo selectedBand;
	private Label showSensorInfoButton;
	private SensorGroupMarker sensorGroupMarker;
	private int allowableDayCount;

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

	private void doSelectBand(Label bandSelectionButton, BandInfo bandInfo,
			VerticalPanel bandDescriptionPanel) {
		//setSelected(true);
		sensorGroupMarker.deselectBandSelectionButtons();

		this.deselectBandSelectionButtons();
		bandSelectionButton.setStyleName("sendButton");
		bandDescriptionPanel.setVisible(true);
		selectedBand = bandInfo;
		sensorInfo.setSelectedBand(bandInfo.getFreqRange().toString());
		setSelected(true);

		logger.finer("minFreq " + bandInfo.getMinFreq() + " maxFreq "
				+ bandInfo.getMaxFreq());
		startDateCalendar.setEnabled(true);
		logger.finer("tEndReadings: " + sensorInfo.gettEndReadings()
				+ " getSelectedStartTime : " + getSelectedStartTime());
		final int maxDayCount = (int) ((double) (selectedBand
				.getTendDayBoundary()
				- getSelectedDayBoundary(getSelectedStartTime()) + getDayBoundaryDelta()) / (double) Defines.SECONDS_PER_DAY) + 1;
		logger.finer("maxDayCount " + maxDayCount);
		allowableDayCount = sensorInfo.getMeasurementType().equals("FFT-Power") ? Math
				.min(14, maxDayCount) : Math.min(30, maxDayCount);

		if (dayCount == -1 || dayCount > allowableDayCount) {
			logger.finer("allowableDayCount : " + allowableDayCount);
			setDayCount(allowableDayCount);
		}
		updateAcquistionCount();
	}

	class SelectBandClickHandler implements ClickHandler {

		private Label bandSelectionButton;
		private BandInfo bandInfo;
		private VerticalPanel bandDescriptionPanel;

		SelectBandClickHandler(VerticalPanel bandDescriptionPanel,
				Label bandSelectionButton, BandInfo bandInfo) {
			this.bandSelectionButton = bandSelectionButton;
			this.bandInfo = bandInfo;
			this.bandDescriptionPanel = bandDescriptionPanel;
		}

		@Override
		public void onClick(ClickEvent event) {
			doSelectBand(bandSelectionButton, bandInfo, bandDescriptionPanel);
		}

	}

	public void updateUserDayCountMenuBar(int dayCount, int maxDayCount) {
		this.dayCount = dayCount;
		userDayCountMenuBar.clearItems();
		int menuBarDayCount = Math.min(allowableDayCount, maxDayCount);
		dayInputSelect.addValueChangedHandler(SensorInfoDisplay.this, menuBarDayCount);
	}

	public void updateReadingsCountLabel(long count) {
		readingsCountLabel.setText(" Acquistions: " + count);
	}

	public void setSelected(boolean flag) {
		selected = flag;
		logger.finer("SensorInfoDisplay: setSelected " + flag + " sensorId = " 
				+ getId() + " bandName = " + sensorInfo.getSelectedBand().getFreqRange().getBandName());
		if (!flag) {
			selectionGrid.remove(startDateCalendar);
			selectionGrid.remove(dayInputSelect);
			selectionGrid.remove(showSensorDataButton);
			selectionGrid.remove(downloadDataButton);
			selectionGrid.remove(showLastCaptureButton);
			selectionGrid.remove(viewCaptureEventsButton);
			selectionGrid.remove(readingsCountLabel);
			selectionGrid.setVisible(false);
			hideAll();
		} else {
			selectionGrid.setWidget(0, 0, startDateCalendar);
			selectionGrid.setWidget(0, 1, dayInputSelect);
			selectionGrid.setWidget(0, 3, readingsCountLabel);
			selectionGrid.setWidget(0, 4, showStatisticsButton);
			if (sensorInfo.isStreamingEnabled()) {
				selectionGrid.setWidget(0, 5, showSensorDataButton);
				selectionGrid.setWidget(0, 6, showLastCaptureButton);
				selectionGrid.setWidget(0, 7, downloadDataButton);
				selectionGrid.setWidget(0, 8, viewCaptureEventsButton);
			} else {
				selectionGrid.setWidget(0, 5, downloadDataButton);
				selectionGrid.setWidget(0, 6, viewCaptureEventsButton);
			}
			spectrumBrowserShowDatasets.hideHelp();
			selectionGrid.setVisible(true);
			// Sensor has not accumulated data yet so dont show irrelevant
			// buttons.
			long count = sensorInfo.getSelectedBand().getCount();
			logger.finer("SensorInfoDisplay: selectedBandName : " + sensorInfo.getSelectedBand().getFreqRange().getBandName() 
						+ " count " + count);
			if (count == 0) {
				startDateCalendar.setVisible(false);
				dayInputSelect.setVisible(false);
				showStatisticsButton.setVisible(false);
				downloadDataButton.setVisible(false);
				showLastCaptureButton.setVisible(false);
			} else {
				startDateCalendar.setVisible(true);
				dayInputSelect.setVisible(true);
				showStatisticsButton.setVisible(true);
				downloadDataButton.setVisible(true);
				showLastCaptureButton.setVisible(true);
			}
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

	public void updateAcquistionCount() {
		// Convert the selected start time to utc
		long startTime = getSelectedStartTime() + dayBoundaryDelta;
		logger.fine("updateAcquistionCount " + startTime + " dayCount "
				+ getDayCount());

		this.selectedBand.updateAcquistionCount(this, startTime, dayCount);
	}
	
	/*public void updateDayTextBox(int dayCount) {
		Window.alert("Made it here with no errors");
		//int newDay = Integer.parseInt(count);
		Window.alert("setDayCount: " + dayCount);
		SensorInfoDisplay.this.setDayCount(dayCount);
		updateAcquistionCount();
		if (dayCount <= 0) {
			logger.log(Level.SEVERE, "Bad day count setting." + dayCount);
			return;
		}
		setDayCount(dayCount);
		 THIS IS WHERE THE TYPE ERROR IS OCCURING -- ANYTIME I TRIED TO UPDATE THE VALUE
		//this.dayCount = dayCount;
		//SensorInfoDisplay.this.setDayCount(dayCount);
		//setDayCount(ac);
	}*/

	public SensorInfoDisplay(final SpectrumBrowser spectrumBrowser,
			final SpectrumBrowserShowDatasets spectrumBrowserShowDatasets,
			double latitude, double longitude, VerticalPanel vpanel,
			VerticalPanel sensorInfoPanel, Grid selectionGrid,
			SensorGroupMarker sensorGroupMarker,
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
			this.selectionButtons = new HashSet<Label>();
			this.bandDescriptionPanels = new HashSet<VerticalPanel>();
			this.sensorGroupMarker = sensorGroupMarker;
			initUiElements();
			// Update the overall data summary of the sensor.
			sensorInfo.updateDataSummary();
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Problem creating SensorInfoDisplay", th);
		}
	}

	void initUiElements() {
		try {
			sensorDescriptionPanel = new VerticalPanel();
			// sensorDescriptionPanel.setTitle("Select a band of interest");
			sensorDescriptionPanel.setVisible(false);
			sensorDescriptionPanel.setBorderWidth(2);
			sensorDescriptionPanel.setStyleName("sensorInformation");

			startDateCalendar = new DateBox();
			startDateCalendar.setFireNullValues(true);
			startDateCalendar.setTitle("Click to select a start date.");
			
			showStatisticsButton = new Button("Generate Daily Occupancy Chart");
			showStatisticsButton.setTitle("Click to generate daily occupancy chart");
			runLengthMenuBar = new MenuBar(true);
			userDayCountMenuBar = new MenuBar(true);
			userDayCountLabel = new Label();
			
			readingsCountLabel = new Label();
			readingsCountLabel.setText("measurements");

			userDayCountMenuBar = new MenuBar(true);
			
			dayInputSelect = new TextInputBox("Duration (days):   ", "");

			showStatisticsButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(
						com.google.gwt.event.dom.client.ClickEvent event) {

					if (isSelected()) {
						if (spectrumBrowserShowDatasets.isFrozen()) {
							Window.alert("Busy generating chart. Please wait.");
						} else {
							long startTime = getSelectedStartTime()
									+ dayBoundaryDelta;
							int days = getDayCount();
							logger.finer("Day Count = " + days
									+ " startTime = " + startTime);
							if (days > 0) {
								spectrumBrowserShowDatasets
										.setStatus("Computing Occupancy Chart -- please wait");
								spectrumBrowserShowDatasets.showWaitImage();
								ArrayList<SpectrumBrowserScreen> navigation = new ArrayList<SpectrumBrowserScreen>();
								navigation
										.add(SensorInfoDisplay.this.spectrumBrowserShowDatasets);

								spectrumBrowserShowDatasets.freeze();

								new DailyStatsChart(
										SensorInfoDisplay.this.spectrumBrowser,
										SensorInfoDisplay.this.spectrumBrowserShowDatasets,
										navigation, getId(), startTime, days,
										sensorInfo.getSelectedBand()
												.getSysToDetect(),
										getMinFreq(), getMaxFreq(),
										getSubBandMinFreq(),
										getSubBandMaxFreq(), sensorInfo
												.getMeasurementType(),
										verticalPanel);
							}
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
					if (spectrumBrowserShowDatasets.isFrozen()) {
						Window.alert("Busy generating chart. Please wait!");
					} else {
						new SensorDataStream(getId(), selectedBand
								.getSystemToDetect(),
								selectedBand.getMinFreq(), selectedBand
										.getMaxFreq(), verticalPanel,
								spectrumBrowser, spectrumBrowserShowDatasets)
								.draw();
					}
				}
			});

			showLastCaptureButton = new Button("Last Capture");

			showLastCaptureButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					if (spectrumBrowserShowDatasets.isFrozen()) {
						Window.alert("Busy generating chart. Please wait!");
					} else {
						SensorInfoDisplay.this.spectrumBrowser
								.getSpectrumBrowserService()
								.getLastAcquisitionTime(getId(),
										selectedBand.getSystemToDetect(),
										selectedBand.getMinFreq(),
										selectedBand.getMaxFreq(),
										new SpectrumBrowserCallback<String>() {

											@Override
											public void onSuccess(String result) {
												JSONValue jsonValue = JSONParser
														.parseLenient(result);
												long selectionTime = (long) jsonValue
														.isObject()
														.get("aquisitionTimeStamp")
														.isNumber()
														.doubleValue();
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
															selectedBand
																	.getSystemToDetect(),
															selectedBand
																	.getMinFreq(),
															selectedBand
																	.getMaxFreq(),
															verticalPanel,
															spectrumBrowser,
															navigation);
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

				}

			});

			downloadDataButton = new Button("Download Data");
			downloadDataButton.setTitle("Click to download data.");
			downloadDataButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					if (spectrumBrowserShowDatasets.isFrozen()) {
						Window.alert("Busy generating chart. Please wait!");
					} else {
						ArrayList<SpectrumBrowserScreen> navigation = new ArrayList<SpectrumBrowserScreen>();
						navigation
								.add(SensorInfoDisplay.this.spectrumBrowserShowDatasets);
						new DowloadData(getId(), tSelectedStartTime, dayCount,
								selectedBand.getSystemToDetect(), selectedBand
										.getMinFreq(), selectedBand
										.getMaxFreq(), verticalPanel,
								SensorInfoDisplay.this.spectrumBrowser,
								navigation).draw();
					}

				}

			});

			viewCaptureEventsButton = new Button("View Capture Events");

			viewCaptureEventsButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					ArrayList<SpectrumBrowserScreen> navigation = new ArrayList<SpectrumBrowserScreen>();
					navigation
							.add(SensorInfoDisplay.this.spectrumBrowserShowDatasets);
					new ViewCaptureEvents(getId(), tSelectedStartTime,
							dayCount, selectedBand.getFreqRange().getBandName(),
							selectedBand.getMinFreq(), selectedBand
									.getMaxFreq(), verticalPanel,
							SensorInfoDisplay.this.spectrumBrowser, navigation);

				}

			}); // TODO -- move this to the admin page maybe?

			startDateCalendar
					.addValueChangeHandler(new ValueChangeHandler<Date>() {

						@Override
						public void onValueChange(ValueChangeEvent<Date> event) {

							Date eventDate = event.getValue();
							if (eventDate == null) {
								Window.alert("Invalid date");
								setSelectedStartTime(sensorInfo
										.gettStartDayBoundary());
								updateAcquistionCount();
								return;
							}
							long dayBoundary = getSelectedDayBoundary(eventDate
									.getTime() / 1000) + getDayBoundaryDelta();
							logger.finer("Calendar valueChanged " + dayBoundary
									+ " sensorInfo.tStartDayBoundary "
									+ sensorInfo.gettStartDayBoundary()
									+ " sensorInfo.tEndReadings "
									+ sensorInfo.gettEndReadings());
							if (dayBoundary < sensorInfo.gettStartDayBoundary()) {
								Window.alert("Date outside available range");
								setSelectedStartTime(sensorInfo
										.gettStartDayBoundary());
								updateAcquistionCount();
							} else if (dayBoundary >= sensorInfo
									.gettEndReadings()) {
								Window.alert("Date beyond available range");
								setSelectedStartTime(sensorInfo
										.gettStartDayBoundary());
								updateAcquistionCount();
							} else {
								logger.finer("Date in acceptable range");
								setSelectedStartTime(getSelectedDayBoundary(eventDate
										.getTime() / 1000));
								updateAcquistionCount();
							}

						}
					});
			showSensorInfoButton = new Label(getId());
			showSensorInfoButton.getElement().getStyle()
					.setCursor(Cursor.POINTER);
			showSensorInfoButton.setStyleName("dangerous");
			showSensorInfoButton.setTitle("Click to show/hide detail");
			showSensorInfoButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					if (sensorDescriptionPanel.isVisible()) {
						sensorDescriptionPanel.setVisible(false);
					} else {
						sensorDescriptionPanel.setVisible(true);
					}
				}

			});

			showSensorInfoButton.setVisible(false);
			sensorInfoPanel.add(showSensorInfoButton);
			sensorInfoPanel.add(sensorDescriptionPanel);

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
		return sensorInfo.getSelectedBand().getMinFreq();
	}

	long getMaxFreq() {
		return sensorInfo.getSelectedBand().getMaxFreq();
	}

	long getSubBandMinFreq() {
		return sensorInfo.getSelectedBand().getSelectedMinFreq();
	}

	long getSubBandMaxFreq() {
		return sensorInfo.getSelectedBand().getSelectedMaxFreq();
	}

	/**
	 * Show the sensor summary information in the side of the map.
	 * 
	 */

	void buildSummary() {
		logger.finer("SensorInfoDisplay: buildSummary " + getId());

		try {

			info = sensorInfo.getSensorDescriptionNoBands();
			sensorDescriptionPanel.add(info);
			for (final String bandName : sensorInfo.getBandNames()) {
				final BandInfo bandInfo = sensorInfo.getBandInfo(bandName);
				if (bandInfo != null) {
					VerticalPanel bandDescriptionPanel = new VerticalPanel();
					HTML bandDescription = sensorInfo
							.getBandDescription(bandName);

					bandDescriptionPanel.add(bandDescription);

					if (sensorInfo.getMeasurementType().equals(
							Defines.SWEPT_FREQUENCY)) {
						bandDescriptionPanel
								.add(new Label("Specify Sub-band :"));
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
											if (!bandInfo
													.setSelectedMinFreq((long) (newFreq * 1E6))) {
												Window.alert("Illegal value entered");
												minFreqBox.setText(Double.toString(bandInfo
														.getSelectedMinFreq() / 1E6));
											}
										} catch (NumberFormatException ex) {
											Window.alert("Illegal Entry");
											minFreqBox.setText(Double.toString(bandInfo
													.getMinFreq() / 1E6));
										}

									}
								});
						minFreqBox.setTitle("Enter value >= "
								+ bandInfo.getMinFreq() / 1E6);
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
														.getSelectedMaxFreq() / 1E6));
											}
										} catch (NumberFormatException ex) {
											Window.alert("Illegal Entry");
											maxFreqBox.setText(Double.toString(bandInfo
													.getSelectedMaxFreq() / 1E6));
										}

									}
								});
						maxFreqBox.setText(Double.toString(bandInfo
								.getSelectedMaxFreq() / 1E6));
						maxFreqBox.setTitle("Enter value <= "
								+ bandInfo.getMaxFreq() / 1E6);
						grid.setWidget(1, 1, maxFreqBox);
						bandDescriptionPanel.add(grid);

						Grid updateGrid = new Grid(1, 2);
						Button changeButton = new Button("Change");
						updateGrid.setWidget(0, 0, changeButton);
						final Label label = new Label();
						updateGrid.setWidget(0, 1, label);
						changeButton.addClickHandler(new ClickHandler() {

							@Override
							public void onClick(ClickEvent event) {
								double minFreq = Double.parseDouble(minFreqBox
										.getText());
								double maxFreq = Double.parseDouble(maxFreqBox
										.getText());

								if (!bandInfo
										.setSelectedMaxFreq((long) (maxFreq * 1E6))
										|| !bandInfo
												.setSelectedMinFreq((long) (minFreq * 1E6))) {
									Window.alert("Illegal value entered");
									minFreqBox.setText(Double.toString(bandInfo
											.getMinFreq() / 1E6));
									maxFreqBox.setText(Double.toString(bandInfo
											.getSelectedMaxFreq() / 1E6));
								} else {
									updateAcquistionCount();
									label.setText("Changes Updated");
									Timer timer = new Timer() {
										@Override
										public void run() {
											label.setText(null);
										}
									};
									timer.schedule(2000);
								}
							}
						});
						bandDescriptionPanel.add(updateGrid);

					}

					final Label bandSelectionButton = new Label(bandInfo
							.getFreqRange().toString());
					bandSelectionButton.getElement().getStyle()
							.setCursor(Cursor.POINTER);
					bandSelectionButton.setStyleName("bandSelectionButton");
					sensorDescriptionPanel.add(bandSelectionButton);
					sensorDescriptionPanel.add(bandDescriptionPanel);
					bandDescriptionPanel.setVisible(false);
					selectionButtons.add(bandSelectionButton);
					bandDescriptionPanels.add(bandDescriptionPanel);
					bandSelectionButton
							.addClickHandler(new SelectBandClickHandler(
									bandDescriptionPanel, bandSelectionButton,
									bandInfo));
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
		dayInputSelect.setValue(Integer.toString(dayCount));
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

	public long getDayBoundaryDelta() {
		return dayBoundaryDelta;
	}

	public HashSet<FrequencyRange> getFreqRanges() {
		return sensorInfo.getFreqRanges();
	}

	public void showSummary(boolean minimize) {
		if (minimize) {
			if (showSensorInfoButton.getParent() == null) {
				sensorInfoPanel.add(showSensorInfoButton);
			}
			showSensorInfoButton.setVisible(true);
			if (sensorDescriptionPanel.getParent() == null) {
				sensorInfoPanel.add(sensorDescriptionPanel);
			}
		} else {
			if (sensorDescriptionPanel.getParent() == null) {
				sensorInfoPanel.add(sensorDescriptionPanel);
			}
			sensorDescriptionPanel.setVisible(true);
		}
		logger.finer("SensorInfoDisplay: showSummary : " + this.getId());
	}

	public void hideAll() {
		sensorDescriptionPanel.setVisible(false);
		showSensorInfoButton.setVisible(false);
		deselectBandSelectionButtons();
	}

	public void deselectBandSelectionButtons() {
		for (Label b : this.selectionButtons) {
			b.setStyleName("bandSelectionButton");
		}
		for (VerticalPanel v : this.bandDescriptionPanels) {
			v.setVisible(false);
		}
	}

}
