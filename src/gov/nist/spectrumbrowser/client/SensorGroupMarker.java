package gov.nist.spectrumbrowser.client;

import java.util.ArrayList;
import java.util.Date;
import java.util.HashSet;
import java.util.logging.Level;
import java.util.logging.Logger;

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
import com.google.gwt.maps.client.overlays.InfoWindow;
import com.google.gwt.maps.client.overlays.InfoWindowOptions;
import com.google.gwt.maps.client.overlays.Marker;
import com.google.gwt.maps.client.overlays.MarkerImage;
import com.google.gwt.maps.client.overlays.MarkerOptions;
import com.google.gwt.user.client.ui.VerticalPanel;

public class SensorGroupMarker {
	private ArrayList<SensorInfoDisplay> sensorInfoCollection = new ArrayList<SensorInfoDisplay>();
	private static ArrayList<SensorGroupMarker> sensorGroupMarkers = new ArrayList<SensorGroupMarker>();
	private double lat;
	private double lon;
	private Marker notSelectedMarker;
	private Marker selectedMarker;
	private static double delta = .05;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	private LatLng position;
	private InfoWindow infoWindow;
	private long lastClicked = 0;

	private SensorGroupMarker(double lat, double lon) {
		this.lat = lat;
		this.lon = lon;
		this.position = LatLng.newInstance(lat, lon);

		String iconPath = SpectrumBrowser.getIconsPath() + "mm_20_red.png";
		logger.finer("lon = " + lon + " lat = " + lat + " iconPath = "
				+ iconPath);
		MarkerImage notSelectedIcon = MarkerImage.newInstance(iconPath);

		notSelectedIcon.setSize(Size.newInstance(12, 20));
		notSelectedIcon.setAnchor(Point.newInstance(6, 20));
		MarkerOptions notSelectedMarkerOptions = MarkerOptions.newInstance();
		notSelectedMarkerOptions.setIcon(notSelectedIcon);
		notSelectedMarkerOptions.setClickable(true);
		notSelectedMarker = Marker.newInstance(notSelectedMarkerOptions);

		// Attach marker to the map.

		notSelectedMarker
				.addMouseOverHandler(new NotSelectedMarkerMouseOverMapHandler());
		notSelectedMarker
				.addMouseOutMoveHandler(new NotSelectedMarkerMouseOutMapHandler());
		notSelectedMarker
				.addMouseDownHandler(new NotSelectedMarkerMouseDownMapHandler());
		notSelectedMarker.setPosition(position);
		notSelectedMarker.setVisible(true);
		notSelectedMarker.setZindex(1);

		// Create icons for the selected marker.
		iconPath = SpectrumBrowser.getIconsPath() + "mm_20_yellow.png";
		MarkerImage selectedIcon = MarkerImage.newInstance(iconPath);
		selectedIcon.setSize(Size.newInstance(12, 20));
		selectedIcon.setAnchor(Point.newInstance(6, 20));
		// create marker options for the selected maker.
		MarkerOptions selectedMarkerOptions = MarkerOptions.newInstance();
		selectedMarkerOptions.setIcon(iconPath);
		selectedMarkerOptions.setClickable(true);

		// Create and attach the selected marker.
		selectedMarker = Marker.newInstance(selectedMarkerOptions);
		selectedMarker.setPosition(position);
		selectedMarker.setVisible(true);
		selectedMarker.setZindex(0);
		
	}
	
	private void detachFromMap() {
		selectedMarker.setMap((MapWidget) null);
		notSelectedMarker.setMap((MapWidget)null);
	}

	private void attachToMap() {
		selectedMarker.setMap(SpectrumBrowserShowDatasets.getMap());
		notSelectedMarker.setMap(SpectrumBrowserShowDatasets.getMap());
	}

	public static SensorGroupMarker create(double lat, double lon,
			VerticalPanel sensorInfoPanel) {
		for (SensorGroupMarker sgm : sensorGroupMarkers) {
			// If within a tolerance, return the marker.
			if (Math.abs(sgm.lat - lat) < delta
					&& Math.abs(sgm.lon - lon) < delta) {
				return sgm;
			}
		}

		SensorGroupMarker retval = new SensorGroupMarker(lat, lon);
		sensorGroupMarkers.add(retval);
		return retval;
	}

	public void addSensorInfo(SensorInfoDisplay sensorInfo) {
		this.sensorInfoCollection.add(sensorInfo);
	}

	public static void clear() {
		for (SensorGroupMarker sgm: sensorGroupMarkers) {
			sgm.detachFromMap();
		}
		
		sensorGroupMarkers.clear();
	}

	public static void showMarkers() {
		logger.finer("SensorGroupMarker: showMarkers");
		for (SensorGroupMarker sgm : sensorGroupMarkers) {
			sgm.attachToMap();
		}
	}


	public void addMouseOverHandler(MouseOverMapHandler mouseOverMapHandler) {
		this.notSelectedMarker.addMouseOverHandler(mouseOverMapHandler);
	}

	public void addMouseOutMoveHandler(MouseOutMapHandler mouseOutMapHandler) {
		this.notSelectedMarker.addMouseOutMoveHandler(mouseOutMapHandler);
	}

	public void addMouseDownHandler(MouseDownMapHandler mouseDownMapHandler) {
		this.notSelectedMarker.addMouseDownHandler(mouseDownMapHandler);

	}

	public void setSelected(boolean flag) {
		logger.finer("SensorGroupMarker: setSelected " + flag);

		attachToMap();

		if (flag) {
			notSelectedMarker.setZindex(0);
			selectedMarker.setZindex(1);
		} else {
			notSelectedMarker.setZindex(1);
			selectedMarker.setZindex(0);
		}
		if (!flag) {
			for (SensorInfoDisplay sid : this.sensorInfoCollection) {
				sid.setSelected(false);
			}
		}
	}

	public static void clearAllSelected() {
		for (SensorGroupMarker sgm : sensorGroupMarkers) {
			sgm.setSelected(false);
		}
	}

	public InfoWindow getInfoWindow(String message) {
		if (infoWindow == null) {
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
			iwo.setPosition(LatLng.newInstance(lat + latitudeOffset, lon));
			iwo.setDisableAutoPan(true);
			iwo.setContent(message);
			infoWindow = InfoWindow.newInstance(iwo);
		}
		return infoWindow;
	}

	private void doMouseDown() {

		for (SensorGroupMarker m : sensorGroupMarkers) {
			if (SensorGroupMarker.this != m)
				m.setSelected(false);
		}

		setSelected(true);

		if (infoWindow != null) {
			infoWindow.close();
		}
		int nSensors = sensorInfoCollection.size();

		for (SensorInfoDisplay sid : sensorInfoCollection) {
			sid.showSummary(nSensors > 1);
		}
	}

	class NotSelectedMarkerMouseOverMapHandler implements MouseOverMapHandler {

		@Override
		public void onEvent(MouseOverMapEvent event) {
			if (sensorInfoCollection.size() == 1) {
				SensorInfoDisplay sensorInfo = sensorInfoCollection.get(0);
				infoWindow = sensorInfo.getInfoWindow();
			} else {
				String message = "<h3>Please click. Multiple sensors for this marker.</h3>";
				infoWindow = getInfoWindow(message);
			}
			infoWindow.open(SpectrumBrowserShowDatasets.getMap());
		}
	}

	class NotSelectedMarkerMouseOutMapHandler implements MouseOutMapHandler {

		@Override
		public void onEvent(MouseOutMapEvent event) {
			if (infoWindow != null)
				infoWindow.close();
		}
	}

	class NotSelectedMarkerMouseDownMapHandler implements MouseDownMapHandler {
		@Override
		public void onEvent(MouseDownMapEvent event) {
			long currentTime = new Date().getTime();
			if (currentTime - lastClicked > 500) {
				lastClicked = currentTime;
				doMouseDown();
			}
		}

	}

	public static void setSelectedSensor(String selectedSensorId) {
		logger.finer("SensorGroupMarker: setSelectedSensor " + selectedSensorId);
		for (SensorGroupMarker sgm : sensorGroupMarkers) {
			for (SensorInfoDisplay sd : sgm.sensorInfoCollection) {
				if (sd.getId().equals(selectedSensorId)) {
					sgm.doMouseDown();
					break;
				}
			}
		}
	}
}
