import junit.framework.*;

public class SimpleJUnitTest extends TestCase
{
	public SimpleJUnitTest(String str)
	{
		super(str);
	}
	
	public void test1()
	{
		SimpleClass s = new SimpleClass();
		assertTrue(s.alwaysTrue());
	}
	
	public static void main(String[] args)
	{
	}
}