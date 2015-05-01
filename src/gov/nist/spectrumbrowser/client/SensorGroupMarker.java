package gov.nist.spectrumbrowser.client;

import java.util.ArrayList;
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
	private Marker marker;
	private MarkerOptions markerOptions;
	private static double delta = .05;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	private LatLng position;
	private boolean isSelected;
	private MarkerImage notSelectedIcon;
	private MarkerImage selectedIcon;
	private InfoWindow infoWindow;
	private VerticalPanel sensorInfoPanel;

	private SensorGroupMarker(double lat, double lon,
			VerticalPanel sensorInfoPanel) {
		this.lat = lat;
		this.lon = lon;
		this.sensorInfoPanel = sensorInfoPanel;
		this.position = LatLng.newInstance(lat, lon);

		String iconPath = SpectrumBrowser.getIconsPath() + "mm_20_red.png";
		logger.finer("lon = " + lon + " lat = " + lat + " iconPath = "
				+ iconPath);
		MarkerImage icon = MarkerImage.newInstance(iconPath);

		icon.setSize(Size.newInstance(12, 20));
		icon.setAnchor(Point.newInstance(6, 20));

		markerOptions = MarkerOptions.newInstance();
		markerOptions.setIcon(icon);

		markerOptions.setClickable(true);
		notSelectedIcon = icon;
		iconPath = SpectrumBrowser.getIconsPath() + "mm_20_yellow.png";
		icon = MarkerImage.newInstance(iconPath);
		icon.setSize(Size.newInstance(12, 20));
		icon.setAnchor(Point.newInstance(6, 20));
		selectedIcon = icon;
		marker = Marker.newInstance(markerOptions);
		marker.addMouseOverHandler(new MyMouseOverMapHandler());
		marker.addMouseOutMoveHandler(new MyMouseOutMapHandler());
		marker.addMouseDownHandler(new MyMouseDownMapHandler());
		marker.setPosition(position);
		marker.setMap(SpectrumBrowserShowDatasets.getMap());
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

		SensorGroupMarker retval = new SensorGroupMarker(lat, lon,
				sensorInfoPanel);
		sensorGroupMarkers.add(retval);
		return retval;
	}

	public void addSensorInfo(SensorInfoDisplay sensorInfo) {
		this.sensorInfoCollection.add(sensorInfo);
	}

	public static void clear() {
		sensorGroupMarkers.clear();
	}

	public static void showMarkers() {
		logger.finer("SensorGroupMarker: showMarkers");
		for (SensorGroupMarker sgm : sensorGroupMarkers) {
			sgm.showMarker();
		}
	}

	public void showMarker() {
		try {
			MapWidget mapWidget = SpectrumBrowserShowDatasets.getMap();
			LatLngBounds bounds = mapWidget.getBounds();
			if (bounds == null) {
				logger.log(Level.SEVERE,
						"showMaker: Bounds not defined for map");
				return;
			}
			if (bounds.contains(position)) {
				logger.fine("SensorGroupMarker: showMarker - bounds contains position");
				marker.setVisible(true);
			} else {
				marker.setVisible(false);
			}
		} catch (Throwable ex) {

			logger.log(Level.SEVERE,
					"showMarker: Error creating sensor marker", ex);
		}
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

	public void setSelected(boolean flag) {
		logger.finer("SensorGroupMarker: setSelected " + flag);

		if (flag == this.isSelected) {
			return;
		}
		this.isSelected = flag;

		if (!flag) {
			marker.setIcon(notSelectedIcon);
			for (SensorInfoDisplay sid : this.sensorInfoCollection) {
				sid.setSelected(false);
			}
		} else {
			marker.setIcon(selectedIcon);
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

	class MyMouseOverMapHandler implements MouseOverMapHandler {

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

	class MyMouseOutMapHandler implements MouseOutMapHandler {

		@Override
		public void onEvent(MouseOutMapEvent event) {
			if (infoWindow != null)
				infoWindow.close();
		}
	}

	class MyMouseDownMapHandler implements MouseDownMapHandler {
		@Override
		public void onEvent(MouseDownMapEvent event) {
			if (isSelected) {
				return;
			}

			sensorInfoPanel.clear();

			for (SensorGroupMarker m : sensorGroupMarkers) {
				if (SensorGroupMarker.this != m)
					m.setSelected(false);
			}

			setSelected(true);

			infoWindow.close();
			int nSensors = sensorInfoCollection.size();

			for (SensorInfoDisplay sid : sensorInfoCollection) {
				sid.showSummary(nSensors > 1);
			}

		}

	}

	public static void setSelectedSensor(String selectedSensorId) {
		for (SensorGroupMarker sgm : sensorGroupMarkers) {
			for (SensorInfoDisplay sd : sgm.sensorInfoCollection){
				if ( sd.getId().equals(selectedSensorId)) {
					sgm.setSelected(true);
					break;
				}
			}
		}
	}
}
