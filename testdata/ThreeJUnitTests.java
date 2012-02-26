import junit.framework.*;

public class ThreeJUnitTests extends TestCase
{
	public ThreeJUnitTests(String str)
	{
		super(str);
	}
	
	public void test1()
	{
		ThreeTestClass s = new ThreeTestClass();
		assertTrue(s.alwaysTrue());
	}
	
	public void test2()
	{
	    ThreeTestClass s = new ThreeTestClass();
	    assertFalse(s.alwaysFalse());
	}
	
	public void test3()
	{
	    ThreeTestClass s = new ThreeTestClass();
	    int a = 500000;
	    assertEquals(a, s.returnInt(a));
	}
	
	public static void main(String[] args)
	{
	}
}