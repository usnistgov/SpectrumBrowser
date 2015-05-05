package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

import java.util.HashSet;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.Scheduler;
import com.google.gwt.event.logical.shared.CloseEvent;
import com.google.gwt.event.logical.shared.CloseHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.maps.client.LoadApi;
import com.google.gwt.maps.client.MapOptions;
import com.google.gwt.maps.client.MapWidget;
import com.google.gwt.maps.client.base.LatLng;
import com.google.gwt.maps.client.base.LatLngBounds;
import com.google.gwt.maps.client.events.zoom.ZoomChangeMapEvent;
import com.google.gwt.maps.client.events.zoom.ZoomChangeMapHandler;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.Window.ClosingEvent;
import com.google.gwt.user.client.Window.ClosingHandler;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HasVerticalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.MenuItem;
import com.google.gwt.user.client.ui.ScrollPanel;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.reveregroup.gwt.imagepreloader.ImagePreloader;

public class SpectrumBrowserShowDatasets implements SpectrumBrowserScreen {
	public static final String END_LABEL = "Available Sensors";
	public static final String LABEL = END_LABEL + " >>";
	SpectrumBrowser spectrumBrowser;
	private VerticalPanel verticalPanel;
	private static MapWidget map = null;
	private HashSet<SensorInfoDisplay> sensorMarkers = new HashSet<SensorInfoDisplay>();
	private HashSet<FrequencyRange> globalFrequencyRanges = new HashSet<FrequencyRange>();
	private HashSet<String> globalSys2Detect = new HashSet<String>();
	private Grid selectionGrid;
	private VerticalPanel sensorInfoPanel;
	private MenuBar navigationBar;
	private MenuBar selectFrequencyMenuBar;
	private MenuBar selectSys2DetectMenuBar;
	private Label helpLabel;


	static Logger logger = Logger.getLogger("SpectrumBrowser");

	private static String selectedSensorId = null;
	
	static {
		 Window.addWindowClosingHandler(new ClosingHandler() {

				@Override
				public void onWindowClosing(ClosingEvent event) {
					
					event.setMessage("Spectrum Browser: Close this window?");

				}
			});
		 Window.addCloseHandler(new CloseHandler<Window> (){

			@Override
			public void onClose(CloseEvent<Window> event) {
				SpectrumBrowser.logoffAllSensors();
			}
			
		 });
	}

	
	
	private HashSet<SensorInfoDisplay> getNeighbors(SensorInfoDisplay sensorMarker) {
		HashSet<SensorInfoDisplay> hs = new HashSet<SensorInfoDisplay>();
		for (SensorInfoDisplay m : getSensorMarkers()) {
			if (Math.abs(m.getLatLng().getLatitude() - sensorMarker.getLatLng().getLatitude()) < 0.05
					&& Math.abs(m.getLatLng().getLongitude() - sensorMarker.getLatLng().getLongitude())<.05) {
				hs.add(m);
			}
		}
		return hs;
	}
	
	

	public SpectrumBrowserShowDatasets(SpectrumBrowser spectrumBrowser,
			VerticalPanel verticalPanel) {
		this.spectrumBrowser = spectrumBrowser;
		this.verticalPanel = verticalPanel;
		ImagePreloader.load(SpectrumBrowser.getIconsPath() + "mm_20_red.png",
				null);
		ImagePreloader.load(
				SpectrumBrowser.getIconsPath() + "mm_20_yellow.png", null);
		
		
		LoadApi.go(new Runnable() {
			@Override
			public void run() {
				draw();
			}
		}, false);

	}

	static MapWidget getMap() {
		return map;
	}

	HashSet<SensorInfoDisplay> getSensorMarkers() {
		return sensorMarkers;
	}

	void setSensorMarkers(HashSet<SensorInfoDisplay> sensorMarkers) {
		this.sensorMarkers = sensorMarkers;
	}


	private void populateMenuItems() {

		selectFrequencyMenuBar = new MenuBar(true);

		MenuItem menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped(
				"Show All").toSafeHtml(), new SelectFreqCommand(null, 0, 0,
				this));
		selectFrequencyMenuBar.addItem(menuItem);

		for (FrequencyRange f : globalFrequencyRanges) {
			menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped(
					Double.toString(f.minFreq / 1E6) + " - "
							+ Double.toString(f.maxFreq / 1E6) + " MHz")
					.toSafeHtml(), new SelectFreqCommand(f.sys2detect,
					f.minFreq, f.maxFreq, this));

			selectFrequencyMenuBar.addItem(menuItem);
		}
		navigationBar.addItem("Show Markers By Frequency Band",
				selectFrequencyMenuBar);

		selectSys2DetectMenuBar = new MenuBar(true);
		menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped("Show All")
				.toSafeHtml(), new SelectBySys2DetectCommand(null, this));
		selectSys2DetectMenuBar.addItem(menuItem);

		for (String sys2detect : globalSys2Detect) {
			menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped(
					sys2detect).toSafeHtml(), new SelectBySys2DetectCommand(
					sys2detect, this));
			selectSys2DetectMenuBar.addItem(menuItem);
		}
		navigationBar.addItem("Show Markers By Detected System",
				selectSys2DetectMenuBar);

		menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped("Help")
				.toSafeHtml(), new Scheduler.ScheduledCommand() {

			@Override
			public void execute() {

			}
		});

		navigationBar.addItem(menuItem);

		menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped("API")
				.toSafeHtml(), new Scheduler.ScheduledCommand() {

			@Override
			public void execute() {
				Window.open(spectrumBrowser.getApiPath() + "index.html", "API",
						null);
			}
		});

		navigationBar.addItem(menuItem);

		menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped("About")
				.toSafeHtml(), new Scheduler.ScheduledCommand() {

			@Override
			public void execute() {

			}
		});
		navigationBar.addItem(menuItem);

		if (spectrumBrowser.isUserLoggedIn()) {
			menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped(
					"Log Off").toSafeHtml(), new Scheduler.ScheduledCommand() {

				@Override
				public void execute() {
					spectrumBrowser.logoff();

				}
			});

			navigationBar.addItem(menuItem);
		}

	}

	public void setStatus(String help) {
		helpLabel.setText(help);
	}

	private void addSensor(JSONObject jsonObj, String baseUrl) {
		try {
			JSONArray locationArray = jsonObj.get("locationMessages").isArray();

			JSONArray systemArray = jsonObj.get("systemMessages").isArray();

			logger.fine("Returned " + locationArray.size()
					+ " Location messages");

			for (int i = 0; i < locationArray.size(); i++) {

				JSONObject jsonObject = locationArray.get(i).isObject();
				String sensorId = jsonObject.get("SensorID").isString()
						.stringValue();
				JSONObject systemMessageObject = null;
				for (int j = 0; j < systemArray.size(); j++) {
					JSONObject jobj = systemArray.get(j).isObject();
					if (jobj.get("SensorID").isString().stringValue()
							.equals(sensorId)) {
						systemMessageObject = jobj;
						break;
					}
				}
				double lon = jsonObject.get("Lon").isNumber().doubleValue();
				double lat = jsonObject.get("Lat").isNumber().doubleValue();
				
				
				JSONArray sensorFreqs;
				
				if (jsonObject.get("sensorFreq") != null) {
					sensorFreqs = jsonObject.get("sensorFreq").isArray();
				} else {
					sensorFreqs = new JSONArray();
					sensorFreqs.set(0, new JSONString("UNDEFINED:0:0"));
				}
				HashSet<FrequencyRange> freqRanges = new HashSet<FrequencyRange>();
				for (int j = 0; j < sensorFreqs.size(); j++) {
					String minMaxFreq[] = sensorFreqs.get(j).isString()
							.stringValue().split(":");
					String sys2detect = minMaxFreq[0];
					long minFreq = Long.parseLong(minMaxFreq[1]);
					long maxFreq = Long.parseLong(minMaxFreq[2]);
					FrequencyRange freqRange = new FrequencyRange(sys2detect,
							minFreq, maxFreq);
					freqRanges.add(freqRange);
					globalFrequencyRanges.add(freqRange);
					globalSys2Detect.add(sys2detect);
				}

				SensorInfoDisplay sensorInfoDisplay = null;
				SensorGroupMarker sensorGroupMarker = SensorGroupMarker.create(lat,lon,sensorInfoPanel);

				for (SensorInfoDisplay sm : getSensorMarkers()) {
					if (sm.getLatLng().getLatitude() == lat
							&& sm.getLatLng().getLongitude() == lon
							&& sm.getId().equals(sensorId)) {
						sensorInfoDisplay = sm;
						break;
					}
				}

				if (sensorInfoDisplay == null) {							
					sensorInfoDisplay = new SensorInfoDisplay(
							SpectrumBrowserShowDatasets.this.spectrumBrowser,
							SpectrumBrowserShowDatasets.this, lat, lon,			
							verticalPanel,
							sensorInfoPanel,
							selectionGrid,
							jsonObject, systemMessageObject, baseUrl);
					getSensorMarkers().add(sensorInfoDisplay);
					sensorGroupMarker.addSensorInfo(sensorInfoDisplay);							
				} 
			}

		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Error drawing marker", th);
		}
	}

	public void showMarkers() {
		if (getSensorMarkers().size() != 0) {
			LatLngBounds bounds = null;

			for (SensorInfoDisplay marker : getSensorMarkers()) {
				if (bounds == null) {
					bounds = LatLngBounds.newInstance(
							marker.getLatLng(),
							marker.getLatLng());
				} else {
					
					bounds.extend(marker.getLatLng());
				}
			}
			LatLng center = bounds.getCenter();
			getMap().setCenter(center);
			getMap().fitBounds(bounds);

			populateMenuItems();
			SensorGroupMarker.showMarkers();
					
		}
		
		if (getSelectedSensor() != null) {
			SensorGroupMarker.setSelectedSensor(getSelectedSensor());
		}
	}
	
	public void draw() {
		try {
			SpectrumBrowser.clearSensorInformation();
			sensorMarkers.clear();
			SensorGroupMarker.clear();
			verticalPanel.clear();
			navigationBar = new MenuBar();
			navigationBar.clearItems();

			verticalPanel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);

			verticalPanel.add(navigationBar);

			HorizontalPanel mapAndSensorInfoPanel = new HorizontalPanel();

			HTML html = new HTML("<h2>" + END_LABEL + "</h2> ", true);

			verticalPanel.add(html);
			String help = "Click on a visible sensor marker to select it. "
					+ "Then select start date and and duration of interest.";
			helpLabel = new Label();
			helpLabel.setText(help);

			verticalPanel.add(helpLabel);
			verticalPanel
					.setTitle("Subset visible sensor markers on map using \"Select Markers By Frequency Band\").\n"
							+ "Click on a visible sensor marker to select it.\n "
							+ "Then select start date and and duration of interest.");

			ScrollPanel scrollPanel = new ScrollPanel();
			scrollPanel.setHeight(SpectrumBrowser.MAP_HEIGHT + "px");
			
			sensorInfoPanel = new VerticalPanel();
			scrollPanel.add(sensorInfoPanel);
			sensorInfoPanel.setStyleName("sensorInfoPanel");
			
			
			mapAndSensorInfoPanel.add(scrollPanel);

			selectionGrid = new Grid(1, 9);
			selectionGrid.setStyleName("selectionGrid");
			selectionGrid.setVisible(false);
			
			for (int i = 0; i < selectionGrid.getRowCount(); i++) {
				for (int j = 0; j < selectionGrid.getColumnCount(); j++) {
					selectionGrid.getCellFormatter().setHorizontalAlignment(i, j,
							HasHorizontalAlignment.ALIGN_CENTER);
					selectionGrid.getCellFormatter().setVerticalAlignment(i, j,
							HasVerticalAlignment.ALIGN_MIDDLE);
				}
			}

			verticalPanel.add(selectionGrid);

			sensorInfoPanel.clear();

			if (map == null) {
				MapOptions mapOptions = MapOptions.newInstance(true);
				mapOptions.setMaxZoom(15);

				map = new MapWidget(mapOptions);
				map.setTitle("Click on marker to select sensor.");
				map.setSize(SpectrumBrowser.MAP_WIDTH + "px",
						SpectrumBrowser.MAP_HEIGHT + "px");
			} else {
				map.removeFromParent();
			}
			mapAndSensorInfoPanel.add(map);
			verticalPanel.add(mapAndSensorInfoPanel);
			logger.finer("getLocationInfo");
			spectrumBrowser.getSpectrumBrowserService().getLocationInfo(
					SpectrumBrowser.getSessionToken(),
					new SpectrumBrowserCallback<String>() {

						@Override
						public void onFailure(Throwable caught) {
							logger.log(Level.SEVERE,
									"Error in processing request", caught);
							verticalPanel.clear();
							
							if (spectrumBrowser.isUserLoggedIn()) {
								Window.alert("The system is down for maintenance. Please try again later.\n"
										 + caught.getMessage());
								spectrumBrowser.logoff();
							} else {
								HTML error = new HTML ("<h1>The System is down for maintenance. Please try later.</h1>");
								verticalPanel.add(error);
								HTML errorMsg = new HTML("<h2>" + caught.getMessage() + "</h2>");
								verticalPanel.add(errorMsg);
							}
						}

						@Override
						public void onSuccess(String jsonString) {

							try {
								logger.finer(jsonString);
								JSONObject jsonObj = (JSONObject) JSONParser
										.parseLenient(jsonString);

								String baseUrl = SpectrumBrowser.getBaseUrlAuthority();
								addSensor(jsonObj, baseUrl);

								logger.finer("Added returned sensors. Dealing with peers");
								// Now deal with the peers.
								final JSONObject peers = jsonObj.get("peers")
										.isObject();
								// By definition, peers do not need login but we need a session
								// Key to talk to the peer so go get one.
								for (String url : peers.keySet()) {
									logger.finer("Showing sensors for Peer " + url);
									final String peerUrl = url;
									spectrumBrowser.getSpectrumBrowserService().isAuthenticationRequired(url,
											new SpectrumBrowserCallback<String>() {

												@Override
												public void onSuccess(
														String result) {
													JSONObject jobj = JSONParser.parseLenient(result).isObject();
													boolean authRequired = jobj.get("AuthenticationRequired").isBoolean().booleanValue();
													if (!authRequired) {
														String sessionToken = jobj.get("SessionToken").isString().stringValue();
														SpectrumBrowser.setSessionToken(peerUrl,sessionToken);
														JSONObject peerObj = peers.get(peerUrl)
																.isObject();
														addSensor(peerObj, peerUrl);
													}
												}

												@Override
												public void onFailure(
														Throwable throwable) {
													logger.log(Level.SEVERE,"Could not contact peer at " + peerUrl,throwable);
												}} );

									
								}
								
								
							
								
								 final Timer timer = new Timer() {
									@Override
									public void run() {
										if (getMap().isAttached()) {
											showMarkers();
											cancel();
										}
									}
								};
								timer.scheduleRepeating(1000);
								//showMarkers();

								map.addZoomChangeHandler(new ZoomChangeMapHandler() {

									@Override
									public void onEvent(ZoomChangeMapEvent event) {
										SensorGroupMarker.showMarkers();
									}
								});
								
								
								

							} catch (Exception ex) {
								logger.log(Level.SEVERE, "Error ", ex);
								spectrumBrowser
										.displayError("Error parsing json response");

							}

						}
					}

			);

		} catch (Exception ex) {
			logger.log(Level.SEVERE, "Error in displaying data sets", ex);
		}
	}

	@Override
	public String getLabel() {
		return LABEL;
	}

	@Override
	public String getEndLabel() {
		return END_LABEL;
	}



	



	public static void setSelectedSensor(String id) {
		logger.finer("SpectrumBrowserShowdatasets: setSelectedSensor : " + id);
		selectedSensorId  = id;
		
	}
	
	public static String getSelectedSensor() {
		return selectedSensorId;
	}



	public static void clearSelectedSensor() {
		selectedSensorId = null;
	}

}
