package gov.nist.spectrumbrowser.client;

import java.util.Date;

import com.google.gwt.event.dom.client.LoadEvent;
import com.google.gwt.event.dom.client.LoadHandler;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.googlecode.gwt.charts.client.ChartLoader;
import com.googlecode.gwt.charts.client.ChartPackage;
import com.googlecode.gwt.charts.client.ColumnType;
import com.googlecode.gwt.charts.client.DataTable;
import com.googlecode.gwt.charts.client.corechart.LineChart;
import com.googlecode.gwt.charts.client.corechart.LineChartOptions;
import com.googlecode.gwt.charts.client.options.HAxis;
import com.googlecode.gwt.charts.client.options.VAxis;
import com.reveregroup.gwt.imagepreloader.FitImage;
import com.reveregroup.gwt.imagepreloader.ImageLoadEvent;
import com.reveregroup.gwt.imagepreloader.ImageLoadHandler;
import com.reveregroup.gwt.imagepreloader.ImagePreloader;

public class StatisticsChart extends VerticalPanel {
	
	private int mWidth;
	private int mHeight;
	private Image image;
	String mUrl;
	
	
	class ImageLoadedHandler implements LoadHandler {

		@Override
		public void onLoad(LoadEvent event) {
			RootPanel.get().remove(image);
			image.setVisible(true);
			StatisticsChart.this.add(image);
			
		}
		
	}

	public StatisticsChart(String url,  int width, int height) {
		mWidth = width;
		mHeight = height;
		mUrl = url;
	}
	
	
	
	public void draw() {
		
		image = new FitImage();
		image.setWidth(mWidth + "px");
		image.setHeight(mHeight + "px");
		image.setVisible(false);
	
	
		if (mUrl != null) {
			ImagePreloader.load(mUrl, new ImageLoadHandler() {

				@Override
				public void imageLoaded(ImageLoadEvent event) {
					image.addLoadHandler(new ImageLoadedHandler());
					image.setUrl(mUrl);
					RootPanel.get().add(image);
					
				} } );
		}
		
	}

	

}
