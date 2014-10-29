package gov.nist.spectrumbrowser.client;

import com.google.gwt.core.client.Scheduler;
import com.google.gwt.maps.client.MapWidget;
import com.google.gwt.maps.client.base.LatLngBounds;

class SelectBySys2DetectCommand implements Scheduler.ScheduledCommand {
	private String sys2Detect;
	private MapWidget map;
	private SpectrumBrowserShowDatasets spectrumBrowserShowDatasets;

	public SelectBySys2DetectCommand(String system2detect, 
			SpectrumBrowserShowDatasets spectrumBrowserShowDatasets) {
		this.sys2Detect = system2detect;
		this.spectrumBrowserShowDatasets = spectrumBrowserShowDatasets;
		this.map = spectrumBrowserShowDatasets.getMap();
	}

	@Override
	public void execute() {
		
		int counter = 0;
		LatLngBounds bounds = map.getBounds();
		for (SensorInformation marker : spectrumBrowserShowDatasets.getSensorMarkers()) {
			if (sys2Detect == null || marker.sys2detect.equals(sys2Detect)) {
				counter ++;
				marker.setVisible(true);
				
				bounds.extend(marker.getLatLng());
			} else {
				marker.setVisible(false);
			}
		}
		if ( counter != 0) {
			map.fitBounds(bounds);
		}
	}

}