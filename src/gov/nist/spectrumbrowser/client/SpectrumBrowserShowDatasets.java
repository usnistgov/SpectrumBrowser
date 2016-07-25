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

import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

import java.util.HashSet;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.Scheduler;
import com.google.gwt.dom.client.Style.Cursor;
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
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HasVerticalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.MenuItem;
import com.google.gwt.user.client.ui.ScrollPanel;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.reveregroup.gwt.imagepreloader.FitImage;
import com.reveregroup.gwt.imagepreloader.ImageLoadEvent;
import com.reveregroup.gwt.imagepreloader.ImageLoadHandler;
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
	private MenuBar navigationBar, selectFrequencyMenuBar, selectSys2DetectMenuBar;
	private Label helpLabel;
	private boolean frozen = false;
	private static String sensorText= "Subset sensor markers on map using:\n "
			+ "\"Show Sensors By Frequency Band\" or \n"
			+ "\"Show Sensors By Detected System\".\n"
			+ "Click on a marker to select a sensor.\n ";
	private static String helpText= "Select to view the help section.";
	static Logger logger = Logger.getLogger("SpectrumBrowser");
	private static String selectedSensorId = null;
	
	public SpectrumBrowserShowDatasets(SpectrumBrowser browser, VerticalPanel verticalPanel) {
		this.spectrumBrowser = browser;
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
		
		Timer timer = new Timer() {

			@Override
			public void run() {
				
				spectrumBrowser.getSpectrumBrowserService().checkSessionTimeout( new SpectrumBrowserCallback<String>() {
					@Override
					public void onSuccess(String result) {
						JSONObject retval = JSONParser.parseLenient(result).isObject();
						String status = retval.get("status").isString().stringValue();
						if (status.equals("NOK")) {
							cancel();
							if (spectrumBrowser.isUserLoggedIn()) {
								spectrumBrowser.logoff();
							} else {
								Window.alert("Your session has expired.");
								spectrumBrowser.logoff();
							}
						}
						
 					}

					@Override
					public void onFailure(Throwable throwable) {
						cancel();
						logger.finer("Session Timer: Error communicating with server -- logging off.");
						if (spectrumBrowser.isUserLoggedIn()) {
							spectrumBrowser.logoff();
						} else {
							spectrumBrowser.logoff();
						}
					}});
 				
			}};
			
		// Check for session timeout every second.
		timer.scheduleRepeating(60*1000);
		

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
		navigationBar.addItem("Show Sensors By Frequency Band",
				selectFrequencyMenuBar);
		navigationBar
		.setTitle("Subset visible sensor markers on map using:\n "
				+ "\"Show Sensors By Frequency Band\" or \n"
				+ "\"Show Sensors By Detected System\".\n"
				+ "Click on a visible marker to select sensors.\n ");

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
		
		navigationBar.addItem("Show Sensors By Detected System",
				selectSys2DetectMenuBar).setTitle(sensorText);;

		menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped("Help")
				.toSafeHtml(), new Scheduler.ScheduledCommand() {

			@Override
			public void execute() {
				Window.open(SpectrumBrowser.getHelpPath(), "Help",
						null);
			}
		});
		menuItem.setTitle(helpText);
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
		helpLabel.setVisible(true);
	}
	
	public void hideHelp() {
		helpLabel.setVisible(false);
	}
	public void showHelp() {
		helpLabel.setVisible(true);
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
				double alt = jsonObject.get("Alt").isNumber().doubleValue();
				
				
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
				logger.log(Level.INFO, "SpectrumBrowserShowDataSets: addSensor : " + sensorId);

				if (sensorInfoDisplay == null) {							
					sensorInfoDisplay = new SensorInfoDisplay(
							SpectrumBrowserShowDatasets.this.spectrumBrowser,
							SpectrumBrowserShowDatasets.this, lat, lon,	alt,	
							verticalPanel,
							sensorInfoPanel,
							selectionGrid,
							sensorGroupMarker,
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

			//populateMenuItems();
			SensorGroupMarker.showMarkers();
					
		}
		
		if (getSelectedSensor() != null) {
			SensorGroupMarker.setSelectedSensor(getSelectedSensor());
		}
	}
	
	public void draw() {
		try {
			spectrumBrowser.showWaitImage();
			Window.setTitle("MSOD:Home");
			SpectrumBrowser.clearSensorInformation();
			sensorMarkers.clear();
			SensorGroupMarker.clear();
			verticalPanel.clear();
			navigationBar = new MenuBar();
			navigationBar.clearItems();

			verticalPanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
			verticalPanel.add(navigationBar);

			HorizontalPanel mapAndSensorInfoPanel = new HorizontalPanel();
			mapAndSensorInfoPanel.setStyleName("mapAndSensorInfoPanel");

			HTML html = new HTML("<h2>" + END_LABEL + "</h2> ", true);

			verticalPanel.add(html);
			String help = "Click on a sensor marker to select it. "
					+ "Then select start date and and duration of interest.";
			helpLabel = new Label();
			helpLabel.setText(help);			
			verticalPanel.add(helpLabel);
			
			ScrollPanel scrollPanel = new ScrollPanel();
			scrollPanel.setHeight(SpectrumBrowser.MAP_WIDTH + "px");
			scrollPanel.setStyleName("sensorInformationScrollPanel");
			
			sensorInfoPanel = new VerticalPanel();
			sensorInfoPanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
			scrollPanel.add(sensorInfoPanel);
			sensorInfoPanel.setStyleName("sensorInfoPanel");
			
			
			mapAndSensorInfoPanel.add(scrollPanel);

			selectionGrid = new Grid(1, 10);
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
			//sensorInfoPanel.setTitle("Click on marker to select sensors.");
			Label selectedMarkersLabel = new Label();
			selectedMarkersLabel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
			selectedMarkersLabel.setText("Sensor Information Display");
			selectedMarkersLabel.getElement().getStyle().setCursor(Cursor.TEXT);
			selectedMarkersLabel.setStyleName("selectedMarkersLabel");
			sensorInfoPanel.add(selectedMarkersLabel);

			if (map == null) {
				MapOptions mapOptions = MapOptions.newInstance(true);
				mapOptions.setMaxZoom(15);
				mapOptions.setMinZoom(3);
				mapOptions.setStreetViewControl(false);
				map = new MapWidget(mapOptions);
				//map.setTitle("Click on a marker to display information about a sensor.");
				map.setSize(SpectrumBrowser.MAP_WIDTH + "px", SpectrumBrowser.MAP_HEIGHT + "px");		
			} else if (map.getParent() != null) {
				map.removeFromParent();
			}
			mapAndSensorInfoPanel.add(map);
			verticalPanel.add(mapAndSensorInfoPanel);
			logger.finer("getLocationInfo");
			
			
			spectrumBrowser.getSpectrumBrowserService().getLocationInfo(SpectrumBrowser.getSessionToken(), new SpectrumBrowserCallback<String>() {
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
											spectrumBrowser.hideWaitImage();
											showMarkers();
											cancel();
										}
									}
								};
								timer.scheduleRepeating(500);
								populateMenuItems();

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
	
	public void freeze() {
		this.frozen  = true;
 	}

	public boolean isFrozen() {
		return this.frozen;
	}
	
	public void unFreeze() {
		this.frozen = false;
	}

}
