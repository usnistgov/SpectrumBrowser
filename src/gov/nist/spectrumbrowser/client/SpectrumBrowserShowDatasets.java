package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;

import java.util.HashSet;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.GWT;
import com.google.gwt.core.client.Scheduler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.maps.client.LoadApi;
import com.google.gwt.maps.client.MapOptions;
import com.google.gwt.maps.client.MapWidget;
import com.google.gwt.maps.client.base.LatLng;
import com.google.gwt.maps.client.base.LatLngBounds;
import com.google.gwt.maps.client.base.Point;
import com.google.gwt.maps.client.base.Size;
import com.google.gwt.maps.client.events.mousedown.MouseDownMapEvent;
import com.google.gwt.maps.client.events.mousedown.MouseDownMapHandler;
import com.google.gwt.maps.client.events.mouseout.MouseOutMapEvent;
import com.google.gwt.maps.client.events.mouseout.MouseOutMapHandler;
import com.google.gwt.maps.client.events.mouseover.MouseOverMapEvent;
import com.google.gwt.maps.client.events.mouseover.MouseOverMapHandler;
import com.google.gwt.maps.client.overlays.MarkerImage;
import com.google.gwt.maps.client.overlays.MarkerOptions;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.MenuItem;
import com.google.gwt.user.client.ui.VerticalPanel;

public class SpectrumBrowserShowDatasets {
	public static final String END_LABEL = "Available Sensors";

	public static final String LABEL = END_LABEL + " >>";

	static final long SECONDS_PER_DAY = 24 * 60 * 60;

	SpectrumBrowser spectrumBrowser;
	VerticalPanel verticalPanel;
	private static MapWidget map;
	private HashSet<SensorInformation> sensorMarkers = new HashSet<SensorInformation>();
	HashSet<FrequencyRange> globalFrequencyRanges = new HashSet<FrequencyRange>();
	private HashSet<String> globalSys2Detect = new HashSet<String>();
	SensorInformation selectedMarker;
	Grid selectionGrid;

	private VerticalPanel sensorInfoPanel;
	

	private MenuBar navigationBar;

	private MenuBar selectFrequencyMenuBar;

	private MenuBar selectSys2DetectMenuBar;

	private Label helpLabel;

	static Logger logger = Logger.getLogger("SpectrumBrowser");

	class MyMouseOverMapHandler implements MouseOverMapHandler {
		private SensorInformation sensorMarker;

		MyMouseOverMapHandler(SensorInformation sensorMarker) {
			this.sensorMarker = sensorMarker;
		}

		@Override
		public void onEvent(MouseOverMapEvent event) {
			sensorMarker.getInfoWindow().open(map);
		}
	}
	
	class MyMouseOutMapHandler implements MouseOutMapHandler{
		
		private SensorInformation sensorMarker;
		MyMouseOutMapHandler(SensorInformation sensorMarker) {
			this.sensorMarker = sensorMarker;
		}
		@Override
		public void onEvent(
				MouseOutMapEvent event) {
			sensorMarker.closeInfoWindow();
		}
	}
	
	class MyMouseDownMapHandler implements MouseDownMapHandler {
		
		private SensorInformation sensorMarker;
		MyMouseDownMapHandler( SensorInformation sensorMarker) {
			this.sensorMarker = sensorMarker;
		}
		@Override
		public void onEvent(
				MouseDownMapEvent event) {
			for (SensorInformation m : getSensorMarkers()) {
				m.setSelected(false);
			}
			sensorMarker.closeInfoWindow();
			sensorMarker.setSelected(true);
			sensorMarker.showSummary();
			selectedMarker = sensorMarker;
		}

	}


	public SpectrumBrowserShowDatasets(SpectrumBrowser spectrumBrowser,
			VerticalPanel verticalPanel) {
		this.spectrumBrowser = spectrumBrowser;
		this.verticalPanel = verticalPanel;
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

	

	HashSet<SensorInformation> getSensorMarkers() {
		return sensorMarkers;
	}

	void setSensorMarkers(HashSet<SensorInformation> sensorMarkers) {
		this.sensorMarkers = sensorMarkers;
	}


	public void setSummaryUndefined() {
		sensorInfoPanel.clear();

	}

	public double getSelectedLatitude() {
		if (selectedMarker != null) {
			return selectedMarker.getLatLng().getLatitude();
		} else
			return (double) -100;
	}

	public double getSelectedLongitude() {
		return selectedMarker != null ? selectedMarker.getLatLng()
				.getLongitude() : -100;
	}

	private void populateMenuItems() {

		MenuItem menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped(
				"Log Off").toSafeHtml(), new Scheduler.ScheduledCommand() {

			@Override
			public void execute() {
				spectrumBrowser.logoff();

			}
		});

		navigationBar.addItem(menuItem);

		selectFrequencyMenuBar = new MenuBar(true);

		menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped(
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
		menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped(
				"Show All").toSafeHtml(), new SelectBySys2DetectCommand(null,
				this));
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

	}
	
	public void setStatus(String help) {
		helpLabel.setText(help);
	}

	public void draw() {
		try {

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

			sensorInfoPanel = new VerticalPanel();
			sensorInfoPanel.setBorderWidth(2);
			mapAndSensorInfoPanel.add(sensorInfoPanel);
			sensorInfoPanel.add(new HTML("<h3>Sensor Information</h3>"));

			selectionGrid = new Grid(1, 9);
			selectionGrid.setStyleName("selectionGrid");
			selectionGrid.setVisible(false);

			verticalPanel.add(selectionGrid);

			setSummaryUndefined();

			if ( map == null) {
				MapOptions mapOptions = MapOptions.newInstance(true);
				mapOptions.setMaxZoom(10);

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
					spectrumBrowser.getSessionId(),
					new SpectrumBrowserCallback<String>() {

						@Override
						public void onFailure(Throwable caught) {
							logger.log(Level.SEVERE,
									"Error in processing request", caught);
							spectrumBrowser.logoff();
						}

						@Override
						public void onSuccess(String jsonString) {

							try {
								logger.finer(jsonString);
								JSONObject jsonObj = (JSONObject) JSONParser
										.parseLenient(jsonString);
								JSONArray locationArray = jsonObj.get(
										"locationMessages").isArray();

								JSONArray systemArray = jsonObj.get(
										"systemMessages").isArray();

								logger.fine("Returned " + locationArray.size()
										+ " Location messages");

								for (int i = 0; i < locationArray.size(); i++) {

									JSONObject jsonObject = locationArray
											.get(i).isObject();
									String sensorId = jsonObject
											.get("SensorID").isString()
											.stringValue();
									JSONObject systemMessageObject = null;
									for (int j = 0; j < systemArray.size(); j++) {
										JSONObject jobj = systemArray.get(j)
												.isObject();
										if (jobj.get("SensorID").isString()
												.stringValue().equals(sensorId)) {
											systemMessageObject = jobj;
											break;
										}
									}
									double lon = jsonObject.get("Lon")
											.isNumber().doubleValue();
									double lat = jsonObject.get("Lat")
											.isNumber().doubleValue();
									if (jsonObject.get("sensorFreq") == null) {
										// TODO -- fix this issue.
										logger.fine("No data found for Sensor -- skipping ");
										continue;
									}
									JSONArray sensorFreqs = jsonObject.get(
											"sensorFreq").isArray();
									HashSet<FrequencyRange> freqRanges = new HashSet<FrequencyRange>();
									for (int j = 0; j < sensorFreqs.size(); j++) {
										String minMaxFreq[] = sensorFreqs
												.get(j).isString()
												.stringValue().split(":");
										String sys2detect = minMaxFreq[0];
										long minFreq = Long
												.parseLong(minMaxFreq[1]);
										long maxFreq = Long
												.parseLong(minMaxFreq[2]);
										FrequencyRange freqRange = new FrequencyRange(
												sys2detect, minFreq, maxFreq);
										freqRanges.add(freqRange);
										globalFrequencyRanges.add(freqRange);
										globalSys2Detect.add(sys2detect);
									}

									LatLng point = LatLng.newInstance(lat, lon);

									String iconPath = SpectrumBrowser
											.getIconsPath() + "mm_20_red.png";
									logger.finer("lon = " + lon + " lat = "
											+ lat + " iconPath = " + iconPath);
									MarkerImage icon = MarkerImage
											.newInstance(iconPath);

									icon.setSize(Size.newInstance(12, 20));
									icon.setAnchor(Point.newInstance(6, 20));

									MarkerOptions options = MarkerOptions
											.newInstance();
									options.setIcon(icon);

									options.setClickable(true);
									SensorInformation marker = null;
									for ( SensorInformation sm : sensorMarkers) {
										if ( sm.getLatLng().equals(point) && sm.getId().equals(sensorId)) {
											marker = sm;
											break;
										}
									}
									
									if ( marker == null) {
										marker = new SensorInformation(
											SpectrumBrowserShowDatasets.this,
											point, options,
											SpectrumBrowserShowDatasets.this.sensorInfoPanel,jsonObject,
											systemMessageObject);
										getSensorMarkers().add(marker);
										marker.setFrequencyRanges(freqRanges);			
										marker.addMouseOverHandler(new MyMouseOverMapHandler(marker));
										marker.addMouseOutMoveHandler(new MyMouseOutMapHandler(marker)); 
										marker.addMouseDownHandler(new MyMouseDownMapHandler(marker)); 
									} else {
										marker.setSensorInfoPanel(sensorInfoPanel);
										marker.setFirstUpdate(true);
									}								
								}
								
								if ( selectedMarker != null) {
									selectedMarker.setSelected(true);
									selectedMarker.showSummary();
								}
								if (getSensorMarkers().size() != 0) {
									LatLngBounds bounds = null;
									
									for (SensorInformation marker : getSensorMarkers()) {
										if (bounds == null) {
											bounds = LatLngBounds.newInstance(marker.getLatLng(), marker.getLatLng());
										} else {
											bounds.extend(marker.getLatLng());
										}
									}
									LatLng center = bounds.getCenter();
									getMap().setCenter(center);
									getMap().fitBounds(bounds);

									populateMenuItems();
								}
							

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

}
